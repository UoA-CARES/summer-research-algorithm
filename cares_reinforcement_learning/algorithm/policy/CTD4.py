"""
CTD4
Continues Distributed TD3
Each Critic outputs a normal distribution

Original Implementation: https://github.com/UoA-CARES/cares_reinforcement_learning/blob/1fce6fcde5183bafe4efce0aa30fc59f630a8429/cares_reinforcement_learning/algorithm/policy/CTD4.py
"""

import copy
import logging
import os
from typing import List, Literal, Tuple

import numpy as np
import torch

from cares_reinforcement_learning.memory import PrioritizedReplayBuffer


class CTD4:
    def __init__(
        self,
        actor_network: torch.nn.Module,
        ensemble_critics: torch.nn.ModuleList,
        gamma: float,
        tau: float,
        action_num: int,
        actor_lr: float,
        critic_lr: float,
        fusion_method: Literal["kalman", "average", "minimum"],
        device: torch.device,
    ):

        self.type = "policy"
        self.device = device

        self.actor_net = actor_network.to(self.device)
        self.target_actor_net = copy.deepcopy(self.actor_net)

        self.ensemble_critics = ensemble_critics.to(self.device)
        self.target_ensemble_critics = copy.deepcopy(self.ensemble_critics)

        self.gamma = gamma
        self.tau = tau

        self.noise_clip = 0.5
        self.policy_noise_decay = 0.999999
        self.min_policy_noise = 0.0

        self.target_policy_noise_scale = 0.2

        self.fusion_method = fusion_method

        self.learn_counter = 0
        self.policy_update_freq = 2

        self.action_num = action_num

        self.actor_lr = actor_lr
        self.actor_net_optimiser = torch.optim.Adam(
            self.actor_net.parameters(), lr=self.actor_lr
        )

        self.lr_ensemble_critic = critic_lr
        self.ensemble_critics_optimizers = [
            torch.optim.Adam(critic_net.parameters(), lr=self.lr_ensemble_critic)
            for critic_net in self.ensemble_critics
        ]
        # -----------------------------------------#

    def select_action_from_policy(
        self, state: np.ndarray, evaluation: bool = False, noise_scale: float = 0.1
    ) -> np.ndarray:
        self.actor_net.eval()
        with torch.no_grad():
            state_tensor = torch.FloatTensor(state).to(self.device)
            state_tensor = state_tensor.unsqueeze(0)
            action = self.actor_net(state_tensor)
            action = action.cpu().data.numpy().flatten()
            if not evaluation:
                noise = np.random.normal(0, scale=noise_scale, size=self.action_num)
                action = action + noise
                action = np.clip(action, a_min=-1, a_max=1)
        self.actor_net.train()
        return action

    def _fusion_kalman(
        self,
        std_1: torch.Tensor,
        mean_1: torch.Tensor,
        std_2: torch.Tensor,
        mean_2: torch.Tensor,
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        kalman_gain = (std_1**2) / (std_1**2 + std_2**2)
        fusion_mean = mean_1 + kalman_gain * (mean_2 - mean_1)
        fusion_variance = (1 - kalman_gain) * (std_1**2)
        fusion_std = torch.sqrt(fusion_variance)
        return fusion_mean, fusion_std

    def _kalman(
        self, u_set: List[torch.Tensor], std_set: List[torch.Tensor]
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        # Kalman fusion
        for i in range(len(u_set) - 1):
            if i == 0:
                x_1, std_1 = u_set[i], std_set[i]
                x_2, std_2 = u_set[i + 1], std_set[i + 1]
                fusion_u, fusion_std = self._fusion_kalman(std_1, x_1, std_2, x_2)
            else:
                x_2, std_2 = u_set[i + 1], std_set[i + 1]
                fusion_u, fusion_std = self._fusion_kalman(
                    fusion_std, fusion_u, std_2, x_2
                )
        return fusion_u, fusion_std

    def _average(
        self, u_set: List[torch.Tensor], std_set: List[torch.Tensor], batch_size: int
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        # Average value among the critic predictions:
        fusion_u = (
            torch.mean(torch.concat(u_set, dim=1), dim=1)
            .unsqueeze(0)
            .reshape(batch_size, 1)
        )
        fusion_std = (
            torch.mean(torch.concat(std_set, dim=1), dim=1)
            .unsqueeze(0)
            .reshape(batch_size, 1)
        )
        return fusion_u, fusion_std

    def _minimum(
        self, u_set: List[torch.Tensor], std_set: List[torch.Tensor], batch_size: int
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        fusion_min = torch.min(torch.concat(u_set, dim=1), dim=1)
        fusion_u = fusion_min.values.unsqueeze(0).reshape(batch_size, 1)
        # # This corresponds to the std of the min U index. That is; the min cannot be got between the stds
        std_concat = torch.concat(std_set, dim=1)
        fusion_std = (
            torch.stack(
                [std_concat[i, fusion_min.indices[i]] for i in range(len(std_concat))]
            )
            .unsqueeze(0)
            .reshape(batch_size, 1)
        )
        return fusion_u, fusion_std

    def train_policy(self, memory: PrioritizedReplayBuffer, batch_size: int) -> None:
        self.learn_counter += 1

        self.target_policy_noise_scale *= self.policy_noise_decay
        self.target_policy_noise_scale = max(
            self.min_policy_noise, self.target_policy_noise_scale
        )

        experiences = memory.sample_uniform(batch_size)
        states, actions, rewards, next_states, dones, _ = experiences

        batch_size = len(states)

        # Convert into tensor
        states = torch.FloatTensor(np.asarray(states)).to(self.device)
        actions = torch.FloatTensor(np.asarray(actions)).to(self.device)
        rewards = torch.FloatTensor(np.asarray(rewards)).to(self.device)
        next_states = torch.FloatTensor(np.asarray(next_states)).to(self.device)
        dones = torch.LongTensor(np.asarray(dones)).to(self.device)

        # Reshape to batch_size
        rewards = rewards.unsqueeze(0).reshape(batch_size, 1)
        dones = dones.unsqueeze(0).reshape(batch_size, 1)

        with torch.no_grad():
            next_actions = self.target_actor_net(next_states)
            target_noise = self.target_policy_noise_scale * torch.randn_like(
                next_actions
            )
            target_noise = torch.clamp(target_noise, -self.noise_clip, self.noise_clip)
            next_actions = next_actions + target_noise
            next_actions = torch.clamp(next_actions, min=-1, max=1)

            u_set = []
            std_set = []
            for target_critic_net in self.target_ensemble_critics:
                u, std = target_critic_net(next_states, next_actions)
                u_set.append(u)
                std_set.append(std)

            if self.fusion_method == "kalman":
                fusion_u, fusion_std = self._kalman(u_set, std_set)
            elif self.fusion_method == "average":
                fusion_u, fusion_std = self._average(u_set, std_set, batch_size)
            elif self.fusion_method == "minimum":
                fusion_u, fusion_std = self._minimum(u_set, std_set, batch_size)

            # Create the target distribution = aX+b
            u_target = rewards + self.gamma * fusion_u * (1 - dones)
            std_target = self.gamma * fusion_std
            target_distribution = torch.distributions.normal.Normal(
                u_target, std_target
            )

        for critic_net, critic_net_optimiser in zip(
            self.ensemble_critics, self.ensemble_critics_optimizers
        ):
            u_current, std_current = critic_net(states, actions)
            current_distribution = torch.distributions.normal.Normal(
                u_current, std_current
            )

            # Compute each critic loss
            critic_individual_loss = torch.distributions.kl.kl_divergence(
                current_distribution, target_distribution
            ).mean()

            # --------- Update Each Critic # ------------#
            critic_net_optimiser.zero_grad()
            critic_individual_loss.backward()
            critic_net_optimiser.step()
            # -------------------------------------------#

        if self.learn_counter % self.policy_update_freq == 0:
            actor_q_u_set = []
            actor_q_std_set = []
            for critic_net in self.ensemble_critics:
                actor_q_u, actor_q_std = critic_net(states, self.actor_net(states))
                actor_q_u_set.append(actor_q_u)
                actor_q_std_set.append(actor_q_std)

            if self.fusion_method == "kalman":
                # ------------------- #
                # kalman filter combination of all critics and then a single mean for the actor loss
                for i in range(len(actor_q_u_set) - 1):
                    if i == 0:
                        x_1_a, std_1_a = actor_q_u_set[i], actor_q_std_set[i]
                        x_2_a, std_2_a = actor_q_u_set[i + 1], actor_q_std_set[i + 1]
                        fusion_u_a, fusion_std_a = self._fusion_kalman(
                            std_1_a, x_1_a, std_2_a, x_2_a
                        )
                    else:
                        x_2_a, std_2_a = actor_q_u_set[i + 1], actor_q_std_set[i + 1]
                        fusion_u_a, fusion_std_a = self._fusion_kalman(
                            fusion_std_a, fusion_u_a, std_2_a, x_2_a
                        )
                # ------------------- #

            elif self.fusion_method == "average":
                # -------------------------------  #
                # average combination of all critics and then a single mean for the actor loss
                fusion_u_a = (
                    torch.mean(torch.concat(actor_q_u_set, dim=1), dim=1)
                    .unsqueeze(0)
                    .reshape(batch_size, 1)
                )
                fusion_std_a = (
                    torch.mean(torch.concat(actor_q_std_set, dim=1), dim=1)
                    .unsqueeze(0)
                    .reshape(batch_size, 1)
                )
                # -------------------------------- #

            elif self.fusion_method == "minimum":
                # -----------------------------------------#
                fusion_min_a = torch.min(torch.concat(actor_q_u_set, dim=1), dim=1)
                fusion_u_a = fusion_min_a.values.unsqueeze(0).reshape(batch_size, 1)
                # This corresponds to the std of the min U index. That is; the min cannot be got between the stds
                std_concat_a = torch.concat(actor_q_std_set, dim=1)
                fusion_std_a = (
                    torch.stack(
                        [
                            std_concat_a[i, fusion_min_a.indices[i]]
                            for i in range(len(std_concat_a))
                        ]
                    )
                    .unsqueeze(0)
                    .reshape(batch_size, 1)
                )
                # -----------------------------------------#

            actor_loss = -fusion_u_a.mean()
            # --------- Update Actor # ------------#
            self.actor_net_optimiser.zero_grad()
            actor_loss.backward()
            self.actor_net_optimiser.step()
            # -------------------------------------#

            # Update ensemble of target critics
            for critic_net, target_critic_net in zip(
                self.ensemble_critics, self.target_ensemble_critics
            ):
                for target_param, param in zip(
                    target_critic_net.parameters(), critic_net.parameters()
                ):
                    target_param.data.copy_(
                        param.data * self.tau + target_param.data * (1.0 - self.tau)
                    )

            # Update target actor
            for target_param, param in zip(
                self.target_actor_net.parameters(), self.actor_net.parameters()
            ):
                target_param.data.copy_(
                    param.data * self.tau + target_param.data * (1.0 - self.tau)
                )

    def save_models(self, filename: str, filepath: str = "models") -> None:
        path = f"{filepath}/models" if filepath != "models" else filepath
        dir_exists = os.path.exists(path)

        if not dir_exists:
            os.makedirs(path)

        torch.save(self.actor_net.state_dict(), f"{path}/{filename}_actor.pht")
        torch.save(
            self.ensemble_critics.state_dict(), f"{path}/{filename}_ensemble.pht"
        )
        logging.info("models has been saved...")

    def load_models(self, filename: str, filepath: str = "models") -> None:
        path = f"{filepath}/models" if filepath != "models" else filepath
        actor_path = f"{path}/{filename}_actor.pht"
        ensemble_path = f"{path}/{filename}_ensemble.pht"

        self.actor_net.load_state_dict(torch.load(actor_path))
        self.ensemble_critics.load_state_dict(torch.load(ensemble_path))
        logging.info("models have been loaded successfully.")

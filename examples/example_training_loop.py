"""
Description:
            This is a basic example of the training loop for the algorithms,
            We may move this later for each repo/env or keep this in this repo
"""

from cares_reinforcement_learning.algorithm import TD3
from cares_reinforcement_learning.networks import Actor
from cares_reinforcement_learning.networks import Critic
from cares_reinforcement_learning.util import MemoryBuffer

import gym
import pandas as pd
import matplotlib.pyplot as plt

import torch
import random
import numpy as np
import logging

logging.basicConfig(level=logging.INFO)

DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
env    = gym.make('Pendulum-v1')

G          = 10
GAMMA      = 0.99
TAU        = 0.005
ACTOR_LR   = 1e-4
CRITIC_LR  = 1e-3
BATCH_SIZE = 32

max_steps_training    = 50_000
max_steps_exploration = 5_000
SEED = 571


def set_seed():
    torch.manual_seed(SEED)
    np.random.seed(SEED)
    random.seed(SEED)
    env.action_space.seed(SEED)


def plot_reward_curve(data_reward):
    data = pd.DataFrame.from_dict(data_reward)
    data.plot(x='step', y='reward', title="Reward Curve")
    plt.show()


def train(agent, memory, max_actions, action_num):
    episode_timesteps = 0
    episode_reward    = 0
    episode_num       = 0

    state, _ = env.reset(seed=SEED)

    historical_reward      = {"episode": [], "episode_reward": []}
    historical_reward_step = {"step": [], "reward": []}

    for total_step_counter in range(int(max_steps_training)):
        episode_timesteps += 1

        if total_step_counter < max_steps_exploration:
            logging.info(f"Running Exploration Steps {total_step_counter}/{max_steps_exploration}")
            action = env.action_space.sample()
        else:
            action = agent.select_action_from_policy(state)
            noise  = np.random.normal(0, scale=0.10 * max_actions, size=action_num)
            action = action + noise
            action = np.clip(action, -max_actions, max_actions)

        next_state, reward, done, truncated, _ = env.step(action)
        memory.add(state, action, reward, next_state, done)

        state = next_state
        episode_reward += reward

        if total_step_counter >= max_steps_exploration:
            for _ in range(G):
                experiences = memory.sample(BATCH_SIZE)
                agent.train_policy(experiences)

        historical_reward_step["step"].append(total_step_counter)
        historical_reward_step["reward"].append(reward)

        if done or truncated:
            logging.info(f"Total T:{total_step_counter+1} Episode {episode_num+1} was completed with {episode_timesteps} steps taken and a Reward= {episode_reward:.3f}")
            historical_reward["episode"].append(episode_num)
            historical_reward["episode_reward"].append(episode_reward)

            # Reset environment
            state, _ = env.reset()
            episode_reward    = 0
            episode_timesteps = 0
            episode_num += 1

    plot_reward_curve(historical_reward_step)


def main():
    observation_size = env.observation_space.shape[0]
    action_num       = env.action_space.shape[0]

    max_actions = env.action_space.high[0]
    min_actions = env.action_space.low[0]

    memory = MemoryBuffer()
    actor  = Actor(observation_size, action_num, ACTOR_LR, max_actions)
    critic = Critic(observation_size, action_num, CRITIC_LR)

    agent = TD3(
        actor_network=actor,
        critic_network=critic,
        max_actions=max_actions,
        min_actions=min_actions,
        gamma=GAMMA,
        tau=TAU,
        device=DEVICE
    )

    set_seed()
    train(agent, memory, max_actions, action_num)


if __name__ == '__main__':
    main()

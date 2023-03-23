"""
Description:
            This is a basic example of the training loop for ON Policy Algorithms,
            We may move this later for each repo/env or keep this in this repo
"""


from cares_reinforcement_learning.algorithm import PPO
from cares_reinforcement_learning.networks.PPO import Actor
from cares_reinforcement_learning.networks.PPO import Critic


import gym
import torch
import random
import logging
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


logging.basicConfig(level=logging.INFO)
DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

env    = gym.make('Pendulum-v1')  # Pendulum-v1, BipedalWalker-v3

G          = 10
GAMMA      = 0.99
ACTOR_LR   = 1e-4
CRITIC_LR  = 1e-3
BATCH_SIZE = 32

max_steps_exploration = 10_000
max_steps_training    = 100_000

SEED = 571

max_steps_per_batch = 400


def train(agent, memory, max_action_value, min_action_value):
    episode_timesteps = 0
    episode_reward    = 0
    episode_num       = 0
    t = 0

    state, _ = env.reset(seed=SEED)

    batch_obs  = []
    batch_acts = []














    for total_step_counter in range(max_steps_training):
        episode_timesteps += 1
        t += 1

        if total_step_counter < max_steps_exploration:
            action = env.action_space.sample()
        else:
            action = env.action_space.sample()  # todo change this and add map

        next_state, reward, done, truncated, _ = env.step(action)
        episode_reward += reward

        if t < max_steps_per_batch:
            batch_obs.append(state)
            batch_acts.append(action)
            # batch the log prob here

        else:
            # all the ppo code here from sample
            logging.info(" completed ")
            t = 0

        state = next_state


        if done or truncated:
            logging.info(f"Total T:{total_step_counter + 1} Episode {episode_num + 1} was completed with {episode_timesteps} steps taken and a Reward= {episode_reward:.3f}")

            # Reset environment
            state, _ = env.reset()
            episode_reward = 0
            episode_timesteps = 0
            episode_num += 1









def main():
    observation_size = env.observation_space.shape[0]
    action_num       = env.action_space.shape[0]

    max_actions = env.action_space.high[0]
    min_actions = env.action_space.low[0]

    memory = None
    actor  = Actor(observation_size, action_num, ACTOR_LR)
    critic = Critic(observation_size, CRITIC_LR)

    agent = PPO(
        actor_network=actor,
        critic_network=critic,
        gamma=GAMMA,
        action_num=action_num,
        device=DEVICE,
    )

    #set_seed()
    train(agent, memory, max_actions, min_actions)



if __name__ == '__main__':
    main()

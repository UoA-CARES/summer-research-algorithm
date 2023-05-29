from cares_reinforcement_learning.memory import MemoryBuffer
from cares_reinforcement_learning.memory.augments import *
from cares_reinforcement_learning.util import helpers as hlp

import time
import gym
import logging

def evaluate_policy_network(env, agent, args):
    evaluation_seed = args["evaluation_seed"]
    max_steps_evaluation = args["max_steps_evaluation"]
    if max_steps_evaluation == 0:
        return

    min_action_value = env.action_space.low[0]
    max_action_value = env.action_space.high[0]

    episode_timesteps = 0
    episode_reward = 0
    episode_num = 0

    env = gym.make(env.spec.id, render_mode="human")
    state, _ = env.reset(seed=evaluation_seed)

    for total_step_counter in range(int(max_steps_evaluation)):
        episode_timesteps += 1
        action = agent.select_action_from_policy(state, evaluation=True)
        action_env = hlp.denormalize(action, max_action_value, min_action_value)

        state, reward, done, truncated, _ = env.step(action_env)
        episode_reward += reward

        if done or truncated:
            logging.info(
                f" Evaluation Episode {episode_num + 1} was completed with {episode_timesteps} steps taken and a Reward= {episode_reward:.3f}")
            # Reset environment
            state, _ = env.reset()
            episode_reward = 0
            episode_timesteps = 0
            episode_num += 1


def policy_based_train(env, agent, memory, args):
    start_time = time.time()

    max_steps_training = args["max_steps_training"]
    max_steps_exploration = args["max_steps_exploration"]
    batch_size = args["batch_size"]
    seed = args["seed"]
    G = args["G"]

    min_action_value = env.action_space.low[0]
    max_action_value = env.action_space.high[0]

    episode_timesteps = 0
    episode_reward = 0
    episode_num = 0

    state, _ = env.reset(seed=seed)
    env.render()

    historical_reward = {"step": [], "episode_reward": []}

    for total_step_counter in range(int(max_steps_training)):
        episode_timesteps += 1

        if total_step_counter < max_steps_exploration:
            logging.info(f"Running Exploration Steps {total_step_counter}/{max_steps_exploration}")
            action_env = env.action_space.sample()  # action range the env uses [e.g. -2 , 2 for pendulum]
            action = hlp.normalize(action_env, max_action_value, min_action_value)  # algorithm range [-1, 1]
        else:
            action = agent.select_action_from_policy(state)  # algorithm range [-1, 1]
            action_env = hlp.denormalize(action, max_action_value,
                                         min_action_value)  # mapping to env range [e.g. -2 , 2 for pendulum]

        next_state, reward, done, truncated, info = env.step(action_env)
        memory.add(state=state, action=action, reward=reward, next_state=next_state, done=done)

        state = next_state
        episode_reward += reward

        if total_step_counter >= max_steps_exploration:
            for _ in range(G):
                experience = memory.sample(batch_size)
                info = agent.train_policy((
                    experience['state'],
                    experience['action'],
                    experience['reward'],
                    experience['next_state'],
                    experience['done']
                ))
                memory.update_priorities(experience['indices'], info)

        if done or truncated:
            logging.info(
                f"Total T:{total_step_counter + 1} Episode {episode_num + 1} was completed with {episode_timesteps} steps taken and a Reward= {episode_reward:.3f}")

            historical_reward["step"].append(total_step_counter)
            historical_reward["episode_reward"].append(episode_reward)

            # Reset environment
            state, _ = env.reset()
            episode_reward = 0
            episode_timesteps = 0
            episode_num += 1

    end_time = time.time()
    elapsed_time = end_time - start_time
    print('Triaining time:', time.strftime("%H:%M:%S", time.gmtime(elapsed_time)))

    hlp.plot_reward_curve(historical_reward)

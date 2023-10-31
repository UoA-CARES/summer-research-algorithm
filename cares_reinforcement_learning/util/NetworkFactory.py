import torch
import logging
from cares_reinforcement_learning.util.configurations import AlgorithmConfig
import sys, inspect

def create_DQN(observation_size, action_num, config: AlgorithmConfig):
    from cares_reinforcement_learning.algorithm.value import DQN
    from cares_reinforcement_learning.networks.DQN import Network

    network = Network(observation_size, action_num)

    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    agent = DQN(
        network=network,
        gamma=config.gamma,
        network_lr=config.lr,
        device=device
    )
    return agent


def create_DuelingDQN(observation_size, action_num, config: AlgorithmConfig):
    from cares_reinforcement_learning.algorithm.value import DQN
    from cares_reinforcement_learning.networks.DuelingDQN import DuelingNetwork

    network = DuelingNetwork(observation_size, action_num)

    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    agent = DQN(
        network=network,
        gamma=config.gamma,
        network_lr=config.lr,
        device=device
    )
    return agent


def create_DoubleDQN(observation_size, action_num, config: AlgorithmConfig):
    from cares_reinforcement_learning.algorithm.value import DoubleDQN
    from cares_reinforcement_learning.networks.DoubleDQN import Network

    network = Network(observation_size, action_num)

    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    agent = DoubleDQN(
        network=network,
        gamma=config.gamma,
        network_lr=config.lr,
        tau=config.tau,
        device=device
    )
    return agent


def create_PPO(observation_size, action_num, config: AlgorithmConfig):
    from cares_reinforcement_learning.algorithm.policy import PPO
    from cares_reinforcement_learning.networks.PPO import Actor
    from cares_reinforcement_learning.networks.PPO import Critic

    actor = Actor(observation_size, action_num)
    critic = Critic(observation_size)

    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    agent = PPO(
        actor_network=actor,
        critic_network=critic,
        actor_lr=config.actor_lr,
        critic_lr=config.critic_lr,
        gamma=config.gamma,
        action_num=action_num,
        device=device
    )
    return agent


def create_SAC(observation_size, action_num, config: AlgorithmConfig):
    from cares_reinforcement_learning.algorithm.policy import SAC
    from cares_reinforcement_learning.networks.SAC import Actor
    from cares_reinforcement_learning.networks.SAC import Critic

    actor = Actor(observation_size, action_num)
    critic = Critic(observation_size, action_num)

    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    agent = SAC(
        actor_network=actor,
        critic_network=critic,
        actor_lr=config.actor_lr,
        critic_lr=config.critic_lr,
        gamma=config.gamma,
        tau=config.tau,
        action_num=action_num,
        device=device,
    )
    return agent


def create_DDPG(observation_size, action_num, config: AlgorithmConfig):
    from cares_reinforcement_learning.algorithm.policy import DDPG
    from cares_reinforcement_learning.networks.DDPG import Actor
    from cares_reinforcement_learning.networks.DDPG import Critic

    actor = Actor(observation_size, action_num)
    critic = Critic(observation_size, action_num)

    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    agent = DDPG(
        actor_network=actor,
        critic_network=critic,
        actor_lr=config.actor_lr,
        critic_lr=config.critic_lr,
        gamma=config.gamma,
        tau=config.tau,
        action_num=action_num,
        device=device,
    )
    return agent


def create_TD3(observation_size, action_num, config: AlgorithmConfig):
    from cares_reinforcement_learning.algorithm.policy import TD3
    from cares_reinforcement_learning.networks.TD3 import Actor
    from cares_reinforcement_learning.networks.TD3 import Critic

    actor = Actor(observation_size, action_num)
    critic = Critic(observation_size, action_num)

    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    agent = TD3(
        actor_network=actor,
        critic_network=critic,
        actor_lr=config.actor_lr,
        critic_lr=config.critic_lr,
        gamma=config.gamma,
        tau=config.tau,
        action_num=action_num,
        device=device,
    )
    return agent

def create_NaSATD3(observation_size, action_num, config: AlgorithmConfig):
    from cares_reinforcement_learning.algorithm.policy import NaSATD3
    from cares_reinforcement_learning.networks.NaSATD3 import Actor
    from cares_reinforcement_learning.networks.NaSATD3 import Critic
    from cares_reinforcement_learning.networks.NaSATD3 import Decoder
    from cares_reinforcement_learning.networks.NaSATD3 import Encoder
    from cares_reinforcement_learning.networks.NaSATD3 import EPDM

    encoder = Encoder(latent_dim=config.latent_size)
    decoder = Decoder(latent_dim=config.latent_size)

    actor = Actor(config.latent_size, action_num, encoder)
    critic = Critic(config.latent_size, action_num, encoder)

    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    agent = NaSATD3(
        encoder_network=encoder,
        decoder_network=decoder,
        actor_network=actor,
        critic_network=critic,
        gamma=config.gamma,
        tau=config.tau,
        action_num=action_num,
        latent_size=config.latent_size,
        intrinsic_on=config.intrinsic_on,
        device=device,
    )
    return agent

class NetworkFactory:
    def create_network(self, observation_size, action_num, config: AlgorithmConfig):
        algorithm = config.algorithm

        '''
        Method taken from:
        https://stackoverflow.com/questions/1796180/how-can-i-get-a-list-of-all-classes-within-current-module-in-python
        '''

        agent = None
        
        for name, obj in inspect.getmembers(sys.modules[__name__]):
            if inspect.isfunction(obj):
                if name == f"create_{algorithm}":
                    agent = obj(observation_size, action_num, config)
        
        if agent is None:
            logging.warn(f"Unkown failed to return None: returned {agent}")
    
        return agent

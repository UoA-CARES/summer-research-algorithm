import torch
from torch import nn
from cares_reinforcement_learning.networks.common import MLP, NoisyLinear
from cares_reinforcement_learning.util.configurations import NoisyNetConfig


class BaseNetwork(nn.Module):
    def __init__(self, network: nn.Module):
        super().__init__()
        self.network = network

    def forward(self, state: torch.Tensor) -> torch.Tensor:
        return self.network(state)

    def reset_noise(self):
        for module in self.network.modules():
            if hasattr(module, "reset_noise"):
                module.reset_noise()


class DefaultNetwork(BaseNetwork):
    def __init__(self, observation_size: int, num_actions: int):
        super().__init__(
            nn.Sequential(
                nn.Linear(observation_size, 64),
                nn.ReLU(),
                NoisyLinear(64, 64, sigma_init=1.0),
                nn.ReLU(),
                NoisyLinear(64, num_actions, sigma_init=0.5),
            )
        )


class Network(BaseNetwork):
    def __init__(self, observation_size: int, num_actions: int, config: NoisyNetConfig):

        network = MLP(
            input_size=observation_size,
            output_size=num_actions,
            config=config.network_config,
        )
        super().__init__(network=network)

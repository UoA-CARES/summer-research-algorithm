from cares_reinforcement_learning.encoders.vanilla_autoencoder import Encoder
from cares_reinforcement_learning.networks.SAC import Critic as SACCritic
from cares_reinforcement_learning.networks.SAC import DefaultCritic as DefaultSACCritic
from cares_reinforcement_learning.networks.common import EncoderCritic
from cares_reinforcement_learning.util.configurations import SACAEConfig


class DefaultCritic(EncoderCritic):
    def __init__(self, observation_size: dict, num_actions: int):

        encoder = Encoder(
            observation_size["image"],
            latent_dim=50,
            num_layers=4,
            num_filters=32,
            kernel_size=3,
        )

        critic = DefaultSACCritic(
            encoder.latent_dim, num_actions, hidden_sizes=[1024, 1024]
        )

        super().__init__(encoder, critic)


class Critic(EncoderCritic):
    def __init__(self, observation_size: dict, num_actions: int, config: SACAEConfig):

        ae_config = config.autoencoder_config
        encoder = Encoder(
            observation_size["image"],
            latent_dim=ae_config.latent_dim,
            num_layers=ae_config.num_layers,
            num_filters=ae_config.num_filters,
            kernel_size=ae_config.kernel_size,
        )

        critic_observation_size = encoder.latent_dim
        if config.vector_observation:
            critic_observation_size += observation_size["vector"]

        critic = SACCritic(critic_observation_size, num_actions, config)

        super().__init__(
            encoder=encoder,
            critic=critic,
            add_vector_observation=bool(config.vector_observation),
        )

from gym.envs.registration import register

register(
    id='Schafkopf-v1',
    entry_point='gym_schafkopf.envs:schafkopf_env',
)

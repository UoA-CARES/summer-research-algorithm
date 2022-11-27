# Summer Reinforcement Learning Package
A python package that allows developers to build and train reinforcement learning models quickly and efficiently.

### Package Structure

```
reinforcement_learning_summer/
├─ agents/
│  ├─ DQNAgent.py
│  ├─ DDPGAgent.py
│  ├─ ...
├─ networks/
│  ├─ Network.py
│  ├─ DuelingNetwork.py
│  ├─ ...
├─ util/
   ├─ train.py
   ├─ plotter.py
   ├─ ...
```
`agents/`: contains reinforcement learning agents that are organised by learning algorithm

`networks/`: contains neural networks that the agents use to approximate

`util/`: contains common utility functions 

### Package Dependencies
Consult the `./requirements.txt` for package dependencies.

Run `pip install -r requirements.txt` to install package requirements

### Usage Notes
Agents interact with the environment via. the [Open AI Gym API](https://www.gymlibrary.dev/content/environment_creation/)

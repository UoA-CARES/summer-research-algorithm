import os
import csv

import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd


class Plotter:

    def write_all_to_file(self, column_title : str, file_name: str, *args):
        """
        Write arrays of data to file
        """

        dir_exists = os.path.exists("raw_data")

        if not dir_exists:
            os.makedirs("raw_data")

        file_out = open(f"raw_data/{file_name}", "w")
        csv_out = csv.writer(file_out)

        csv_out.writerow(column_title)
        for row in zip(*args):
            csv_out.writerow(row)

    def write_to_file(self, file_name: str, *args):
        """
        Write single instance to file
        """
        dir_exists = os.path.exists("raw_data")

        if not dir_exists:
            os.makedirs("raw_data")

        file_out = open(f"raw_data/{file_name}", "a")
        csv_out = csv.writer(file_out)

        csv_out.writerow(args)

    def plot_learning(self, title: str, reward):
        y = reward
        x = range(1, len(reward) + 1)

        print(reward)
        print(x)

        data_dict = {"Episode": x, "Reward": y}
        df = pd.DataFrame(data=data_dict)

        sns.set_theme(style="darkgrid")
        plt.figure().set_figwidth(8)

        sns.lineplot(data=df, x="Episode", y="Reward")
        plt.title(title)
        plt.show()

    def plot_learning_average(self, title: str, reward):
        y = reward
        x = range(1, len(reward) + 1)

        print(reward)
        print(x)

        data_dict = {"Episode": x, "Reward": y}
        df = pd.DataFrame(data=data_dict)

        df["Average Reward"] = df["Reward"].rolling(10).mean()

        sns.set_theme(style="darkgrid")
        plt.figure().set_figwidth(8)

        sns.lineplot(data=df, x="Episode", y="Reward", alpha=0.4)
        sns.lineplot(data=df, x="Episode", y="Average Reward")

        plt.fill_between(df["Episode"], df["Reward"], df["Average Reward"], alpha=0.4)
        plt.title(title)

        plt.show()

    def plot_average_std(self, title: str, reward):
        y = reward
        x = range(1, len(reward) + 1)

        data_dict = {"Episode": x, "Reward": y}
        df = pd.DataFrame(data=data_dict)

        df["Average Reward"] = df["Reward"].rolling(10).mean()
        df["Standard Deviation"] = df["Reward"].rolling(10).std()

        sns.set_theme(style="darkgrid")
        plt.figure().set_figwidth(8)

        ax = sns.lineplot(data=df, x="Episode", y="Average Reward", label="Average Reward")
        ax.set(xlabel="Episode", ylabel="Reward")
        plt.fill_between(df["Episode"], df["Average Reward"] - df["Standard Deviation"], df["Average Reward"] +
                         df["Standard Deviation"], alpha=0.4)

        sns.move_legend(ax, "lower right")

        plt.title(title)
        plt.show()

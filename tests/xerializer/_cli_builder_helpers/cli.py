from xerializer import serializable, cli_builder
import json
from xerializer._argparse import Argument


@serializable(signature="DmyTrainManager")
class DmyTrainManager:
    def __init__(self, filename):
        self.filename = filename

    def run(self, text1, text2):
        with open(self.filename, "w") as fo:
            json.dump({"text1": text1, "text2": text2}, fo)


if __name__ == "__main__":
    cli_builder.hydra_cli(
        lambda x, **kwargs: x.run(**kwargs),
        cli_args=[Argument("text1"), Argument("--text2"), Argument("--text3")],
        excluded_cli_args=["text3"],
    )[0]()

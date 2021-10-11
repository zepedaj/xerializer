from xerializer import serializable, cli_builder


@serializable(signature='DmyTrainManager')
class DmyTrainManager:
    def __init__(self, filename):
        self.filename = filename

    def run(self):
        with open(self.filename, 'w') as fo:
            fo.write('Text.')


if __name__ == '__main__':
    cli_builder.hydra_cli(lambda x: x.run())

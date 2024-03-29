"""Utility functions."""

import os
import ast
from datetime import datetime


# Custom argparser.
def str_to_float(argument):
    """Infer numeric type from string."""
    out = argument
    try:
        if argument.lower() == 'true':
            out = True
        if argument.lower() == 'false':
            out = False

        elif ('.' in argument) or ('e' in argument.lower()):
            out = float(argument)
        else:
            out = int(argument)

    except Exception:
        pass

    return out


def str_to_attr(argument):
    """Convert string to attribute."""
    out = argument
    try:
        out = ast.literal_eval(argument)
    except Exception:
        pass

    return out


def load_args(config, sh_args):
    """Set attributes of config class given dict of args."""
    for k, v in sh_args.items():
        try:
            config.__getattribute__(k)
            setattr(config, k, str_to_attr(v))
        except Exception as e:
            print(e)
    return config


class ExperimentLogger():
    """Log performance of model instance.

    ExperimentLogger is used by Trainer.
    """

    def __init__(self, config, attributes=None, log_str=None):
        """Initialise experiment folder."""
        self.c = config

        # Logged quantitites.
        if attributes is None:
            self.attributes = \
                ['step', 'time', 'elbo', 'reward', 'min_ll',
                 'bg', 'patch', 'overlap', 'log_q', 'translik',
                 'error', 'std_error',
                 'scale_x', 'scale_y',
                 'v_error', 'std_v_error',
                 'z_std_0', 'z_std_1', 'z_std_2', 'z_std_3', 'z_std_4', 'z_std_5',
                 'swaps', 'type']
        else:
            self.attributes = attributes

        # Formatting.
        if log_str is None:
            self.log_str = '{:d},' + (len(self.attributes) - 2) * '{:.5f},' + '{}\n'
        else:
            self.log_str = log_str

        self.performance_str = ','.join(self.attributes)+'\n'

        # Make Experiment folder and save config.
        if not self.c.nolog:
            self.exp_dir = self.make_dir()
            self.img_dir = os.path.join(self.exp_dir, 'imgs')
            os.makedirs(self.img_dir)
            self.save_config()

            self.performance_file = os.path.join(self.exp_dir, 'performance.csv')

            with open(self.performance_file, 'w') as f:
                f.write(self.performance_str)

        else:
            self.exp_dir = os.path.join(self.c.experiment_dir, 'tmp')
            print('logging disabled')

    def make_dir(self):
        """Find current run number and create folder."""
        exp_dir = os.path.join(
            self.c.experiment_dir,
            'run{:03d}'
            )
        current = exp_dir.format(0)
        i = 1
        while os.path.exists(current):
            current = exp_dir.format(i)
            i += 1
        os.makedirs(current)
        print('Logging to directory {}'.format(current))
        return current

    def save_config(self):
        """Save StoveConfig file as txt."""
        file = os.path.join(self.exp_dir, 'config.txt')
        with open(file, 'a') as f:
            f.write('setting name, setting value\n')
            for setting in self.c.__dir__():
                if not setting.startswith('__'):
                    attribute = self.c.__getattribute__(setting)
                    if isinstance(attribute, list):
                        f.write('{},"{}"\n'.format(setting, attribute))
                    else:
                        f.write('{},{}\n'.format(setting, attribute))

            branch = os.popen("git rev-parse --abbrev-ref HEAD").read()[:-1]
            f.write('{},{}\n'.format('branch', branch))
            commit = os.popen("git rev-parse HEAD").read()[:-1]
            f.write('{},{}\n'.format('commit', commit))
            time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            f.write('{},{}\n'.format('time', time))

    def performance(self, perf_dict):
        """Log the performance for a given performance dictionary.

        Valid perf_dict created by trainer.error_and_log().

        """
        # extract data from performance dict
        # return NaN if not available
        values = [perf_dict.get(attribute, float('nan')) for attribute in self.attributes]

        log_str = self.log_str.format(*values)

        print(self.performance_str)
        print(log_str)
        if not self.c.nolog:
            with open(self.performance_file, 'a') as f:
                f.write(log_str)

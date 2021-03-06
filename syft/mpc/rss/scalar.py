from .config import PrecisionConfig
import numpy as np
import random

Q = 293973345475167247070445277780365744413


class MPCNatural(object):

    def __init__(self, id, repo):
        self.id = id
        self.repo = repo

    def __add__(self, id):
        new_id = self.gen_rand_id()
        return self.repo.add(new_id, self.id, id.id, True)

    def __mul__(self, x):
        new_id = self.gen_rand_id()

        if(type(x) == type(self)):
            return self.repo.mult(new_id, self.id, x.id, True)
        else:
            return self.repo.mult_scalar(new_id, self.id, x, True)

    def __repr__(self):
        return str(self.get())

    def __sub__(self, id):
        new_id = self.gen_rand_id()
        return self.repo.sub(new_id, self.id, id.id, True)

    def __truediv__(self, x):
        new_id = self.gen_rand_id()
        if(type(x) == type(self)):
            return NotImplemented
        else:
            return self.repo.div_scalar(new_id, self.id, x, True)

    def gen_rand_id(self, length=2**32):
        return np.random.randint(0, length)

    def get(self):
        return sum(self.get_shares()) % Q

    def get_shares(self):
        others = list(map(lambda x: x.get_share(self.id), self.repo.siblings))
        return others + [self.repo.ints[self.id]]


class MPCFixedPoint(object):

    def __init__(self, raw, repo, config=None, raw_natural=None):

        if(config is None):
            self.config = PrecisionConfig()
        else:
            self.config = config

        self.repo = repo
        if(raw_natural is None):
            self.raw_natural = self.repo.create_natural(self.encode(raw))
        else:
            self.raw_natural = raw_natural

    def __add__(self, x):

        if(type(x) != type(self)):
            x = MPCFixedPoint(x, self.repo, config=self.config)

        return MPCFixedPoint(None, self.repo, raw_natural=self.raw_natural + x.raw_natural)

    def __mul__(self, x):

        if(type(x) != type(self)):
            return MPCFixedPoint(None, self.repo, raw_natural=(self.raw_natural * self.encode(x))).truncate()
        else:
            return MPCFixedPoint(None, self.repo, raw_natural=(self.raw_natural * x.raw_natural)).truncate()

    def __repr__(self):
        return str(self.get())

    def __sub__(self, x):

        if(type(x) != type(self)):
            x = MPCFixedPoint(x, self.repo, config=self.config)

        return self.raw_natural - x.raw_natural

    def __truediv__(self, x):

        return self.raw_natural.__truediv__(self.encode(x))

    def decode(self, field_element):
        upscaled = field_element if field_element <= self.config.Q / 2 else field_element - self.config.Q
        rational = upscaled / self.config.BASE**self.config.PRECISION_FRACTIONAL
        return rational

    def encode(self, rational):
        upscaled = int(rational * self.config.BASE**self.config.PRECISION_FRACTIONAL)
        field_element = upscaled % self.config.Q
        return field_element

    def get(self):
        return self.decode(self.raw_natural.get()) % self.config.Q

    def truncate(self):

        b = self.raw_natural + self.repo.create_natural_with_shares([self.config.BASE**(2 * self.config.PRECISION + 1), 0, 0])
        mask = random.randrange(self.config.Q) % self.config.BASE**(self.config.PRECISION + self.config.PRECISION_FRACTIONAL + self.config.KAPPA)
        mask_low = mask % self.config.BASE**self.config.PRECISION_FRACTIONAL
        b_masked = (b + self.repo.create_natural_with_shares([mask, 0, 0])).get()
        b_masked_low = b_masked % self.config.BASE**self.config.PRECISION_FRACTIONAL
        b_low = self.repo.create_natural(b_masked_low) - self.repo.create_natural(mask_low)
        c = self.raw_natural - b_low
        d = c * self.config.INVERSE
        self.raw_natural = d

        return self

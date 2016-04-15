'''
Low-level programming constructs for key-value stores

Originally developed as part of Zephyr
https://zephyr.space/
'''

import warnings
import numpy as np
from functools import reduce


class ClassProperty(property):
    '''
    Class decorator to enable property behaviour in classes
    '''

    def __get__(self, cls, owner):
        return self.fget.__get__(None, owner)()


class AMMetaClass(type):
    '''
    Meta class that enables AttributeMapper functionality, including inheritance
    in the dictionary 'initMap'.
    '''

    def __new__(mcs, name, bases, attrs):
        'Build a new subclass of AttributeMapper'

        baseMaps = [getattr(base, 'initMap', {}) for base in bases][::-1]
        baseMaps.append(attrs.get('initMap', {}))

        initMap = {}
        for baseMap in baseMaps:
            initMap.update(baseMap)
            for key in initMap:
                if initMap[key] is None:
                    del(initMap[key])

        attrs['initMap'] = initMap

        baseMasks = reduce(set.union, (getattr(base, 'maskKeys', set()) for base in bases))
        maskKeys = set.union(baseMasks, attrs.get('maskKeys', set()))

        if maskKeys:
            attrs['maskKeys'] = maskKeys

        return type.__new__(mcs, name, bases, attrs)

    def __call__(cls, *args, **kwargs):
        'Instantiate a subsclass of AttributeMapper'

        if not args:
            raise TypeError('__init__() takes at least 2 arguments (1 given)')
        systemConfig = args[0]

        obj = cls.__new__(cls)

        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            for key in obj.initMap.keys():
                if (key not in systemConfig) and obj.initMap[key][0]:
                    raise ValueError('Class {0!s} requires parameter \'{1!s}\''.format(cls.__name__, key))
                if key in systemConfig:
                    if obj.initMap[key][2] is None:
                        def typer (x):
                            return x
                    else:
                        def typer(x):
                            newtype = obj.initMap[key][2]
                            try:
                                return obj.initMap[key][2](x)
                            except TypeError:
                                if np.iscomplex(x) and issubclass(newtype, np.floating):
                                    return typer(x.real)
                                raise

                    if obj.initMap[key][1] is None:
                        setattr(obj, key, typer(systemConfig[key]))
                    else:
                        setattr(obj, obj.initMap[key][1], typer(systemConfig[key]))

        obj.__init__(*args, **kwargs)
        return obj


class AttributeMapper(object):
    '''
    An AttributeMapper subclass defines a dictionary initMap, which
    includes keys for mappable inputs expected from the systemConfig
    parameter. The dictionary takes the form:

    initMap = {
    #   Argument        Required    Rename as ...   Store as type
        'c':            (True,      '_c',           np.complex128),
        'rho':          (False,     '_rho',         np.float64),
        'freq':         (True,      None,           np.complex128),
        'dx':           (False,     '_dx',          np.float64),
        'dz':           (False,     '_dz',          np.float64),
        'nx':           (True,      None,           np.int64),
        'nz':           (True,      None,           np.int64),
        'freeSurf':     (False,     '_freeSurf',    list),
    }

    Each value in the dictionary is a tuple, which is interpreted by
    the metaclass (i.e., AMMetaClass) to determine how to process the
    value corresponding to the same key in systemConfig.

    An exception will be raised if the first element in the tuple
    is set to true, but the corresponding key does not exist in the
    systemConfig parameter.

    If the second element in the tuple is set to None, the key will be
    defined in the subclass's attribute dictionary as it stands, whereas
    if the second element is a string then that overrides the key.

    If the third element in the tuple is set to None, the input argument
    will be set in the subclass dictionary unmodified; however, if the
    third element is a callable then it will be applied to the element
    (e.g., to allow copying and/or typecasting of inputs).

    NB: Complex numpy arguments are handled specially: the real part of
    the value is kept and the imaginary part is discarded when they are
    typecast to a float.
    '''

    __metaclass__ = AMMetaClass

    def __init__(self, systemConfig):
        '''
        AttributeMapper(systemConfig)

        Args:
            systemConfig (dict): A set of setup keys
        '''

        pass

    @ClassProperty
    @classmethod
    def required(cls):
        'Property to return required fields in initMap'

        return {key for key in cls.initMap if cls.initMap[key][0]}

    @ClassProperty
    @classmethod
    def optional(cls):
        'Property to return optional fields in initMap'

        return {key for key in cls.initMap if not cls.initMap[key][0]}


class SCFilter(object):
    '''
    A SCFilter class is initialized with a list of classes as arguments.
    For any of those classes that are AttributeMapper subclasses, SCFilter
    determines the required fields in their initMap trees, and the optional
    fields. When called, the SCFilter discards any key in the passed dictionary
    that does not match one of those fields, and raises an error if any of the
    required fields are not present.
    '''

    def __init__(self, clslist):
        '''
        SCFilter(clslist)

        Args:
            clslist (list): List of classes from which to build the filter

        Returns:
            new SCFilter instance
        '''

        if not hasattr(clslist, '__contains__'):
            clslist = [clslist]

        self.required = reduce(set.union, (cls.required for cls in clslist if issubclass(cls, AttributeMapper)))
        self.optional = reduce(set.union, (cls.optional for cls in clslist if issubclass(cls, AttributeMapper)))
        self.optional.symmetric_difference_update(self.required)

    def __call__(self, systemConfig):
        '''
        Args:
            systemConfig (dict): A systemConfig dictionary to filter

        Returns:
            dict: Filtered dictionary

        Raises:
            ValueError: If a required key is not in the systemConfig
        '''

        for key in self.required:
            if key not in systemConfig:
                raise ValueError('{0!s} requires parameter \'{1!s}\''.format(cls.__name__, key))

        return {key: systemConfig[key] for key in set.union(self.required, self.optional) if key in systemConfig}


class BaseSCCache(AttributeMapper):
    '''
    Subclass of AttributeMapper that caches (a filtered version of) the
    systemConfig object used to initialize it.
    '''

    maskKeys = set()
    cacheItems = []

    def __init__(self, systemConfig):

        super(BaseSCCache, self).__init__(systemConfig)
        self.systemConfig = {key: systemConfig[key] for key in systemConfig if key not in self.maskKeys}

    @property
    def systemConfig(self):
        return self._systemConfig
    @systemConfig.setter
    def systemConfig(self, value):
        self._systemConfig = value
        self.clearCache()

    def clearCache(self):
        'Clears cached items (e.g., when model is reset).'
        for attr in self.cacheItems:
            if hasattr(self, attr):
                delattr(self, attr)

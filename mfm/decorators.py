# #
# # import warnings
# import functools
# import os
# from qtpy import uic
#
#
#
# def load_ui(ui_file):
#     """This is a decorator which can be used to mark functions
#     as deprecated. It will result in a warning being emitted
#     when the function is used."""
#
#     def new_func(func, *args, **kwargs):
#         super(func.__class__, ).__init__(*args, **kwargs)
#         uic.loadUi(
#             os.path.join(
#                 os.path.dirname(os.path.abspath(func.__module__.__file__)),
#                 ui_file
#             ),
#             args[0]
#         )
#         return func(*args, **kwargs)
#
#     return new_func
#

#
# def deprecated(func):
#     """This is a decorator which can be used to mark functions
#     as deprecated. It will result in a warning being emitted
#     when the function is used."""
#     @functools.wraps(func)
#     def new_func(*args, **kwargs):
#         warnings.simplefilter('always', DeprecationWarning)  # turn off filter
#         warnings.warn("Call to deprecated function {}.".format(func.__name__),
#                       category=DeprecationWarning,
#                       stacklevel=2)
#         warnings.simplefilter('default', DeprecationWarning)  # reset filter
#         return func(*args, **kwargs)
#     return new_func
#
#
# def register(*args, **kwargs):
#
#     def class_rebuilder(cls):
#
#         #@wraps(cls)
#         class RegisteredClass(cls):
#
#             _instances = kwargs.get('instances', set())
#
#             @classmethod
#             def getinstances(cls):
#                 """Returns all instances of the class as an generator
#                 """
#                 dead = set()
#                 for ref in cls._instances:
#                     obj = ref()
#                     if obj is not None:
#                         yield obj
#                     else:
#                         dead.add(ref)
#                 cls._instances -= dead
#
#             def __init__(self, *args, **kwargs):
#                 self._instances.add(weakref.ref(self))
#                 #super(cls.mro()[1], self).__init__(*args, **kwargs)
#                 #RegisteredClass.mro()[1].__init__(self, *args, **kwargs)
#                 super(RegisteredClass, self).__init__(*args, **kwargs)
#                 #super(cls, self).__init__(*args, **kwargs)
#                 #cls.__init__(self, *args, **kwargs)
#
#             def __getattribute__(self, attr_name):
#                 obj = super(RegisteredClass, self).__getattribute__(attr_name)
#                 if hasattr(obj, '__call__') and attr_name == '_instances':
#                     return self._instances
#                 return obj
#
#             #def __repr__(self):
#             #    return super(RegisteredClass, self).__repr__()
#
#         try:
#             RegisteredClass.__doc__ = cls.__doc__
#         except AttributeError:
#             pass
#         return RegisteredClass
#
#     return class_rebuilder


def set_module(module):
    """Decorator for overriding __module__ on a function or class.

    Example usage::

        @set_module('numpy')
        def example():
            pass

        assert example.__module__ == 'numpy'
    """
    def decorator(func):
        if module is not None:
            func.__module__ = module
        return func
    return decorator


from redengine.parse import parse_session
from redengine.parse.utils import instances, ParserPicker
from redengine.core.meta import _register

CLS_EXTENSIONS = {}
PARSERS = {}

def _get_parser(init_method):
    return ParserPicker(
        {
            dict: instances.DictParser(instance_parser=init_method, key_as_arg="name"),
            list: instances.ListParser(instance_parser=init_method)
        }
    )

class _ExtensionMeta(type):
    def __new__(mcs, name, bases, class_dict):

        cls = type.__new__(mcs, name, bases, class_dict)

        # Store the name and class for configurations
        parse_key = getattr(cls, "__parsekey__", None)
        if parse_key is not None:
            parser = _get_parser(cls.parse_cls)
            parse_session[parse_key] = parser
            PARSERS[parse_key] = parser
        _register(cls, CLS_EXTENSIONS)
        return cls

class BaseExtension(metaclass=_ExtensionMeta):
    """Base for all extensions that are registered
    to the sessions and are parsable in configs.

    An extension is an external components that 
    extends the existing behaviour of Red Engine.
    They are stored in the session objects so 
    that they are accessible from other extensions
    and tasks.
    
    An extension could be:

        - A pipeline: adds conditions to all given tasks 
          so that they are executed one after another.
        - A task group: so that some attributes of a 
          set of tasks can be changed at once. 
        - Named resources: sets additional parameters to
          given tasks.


    Warnings
    ---------
    Extensions are experimential and subject to change
    somewhat in newer versions.


    Parameters
    ----------
    name : str
        Name of the extension instance.
    session : redengine.Session
        Session object for which the extension is for.

    Notes
    -----
    Red Engine also has :ref:`hooks <hooks>`. that are simpler way to extend
    the framework.

    List of hooks:

        - redengine.core.Task.hook_init
        - redengine.core.Scheduler.hook_startup
        - redengine.core.Scheduler.hook_cycle
        - redengine.core.Scheduler.hook_shutdown

    Examples
    --------

    Minimum example:

    >>> from redengine.core import BaseExtension
    >>> class MyExtension(BaseExtension):
    ...     __parsekey__ = 'myextensions'
    ...
    ...     def at_parse(self, thing):
    ...         self.thing = thing
    ...         ... # What the extension does.
    ...
    ...     def __repr__(self):
    ...         return f"MyExtension('{self.thing}')"
    ...
    >>> from redengine.config import parse_session
    >>> session = parse_session({
    ...     "myextensions": [
    ...         {"thing": "hat", 'name': 'my_instance'}
    ...     ]
    ... })
    >>> session.extensions
    {'myextensions': {'my_instance': MyExtension('hat')}}

    """
    session: 'Session'
    __parsekey__: str
    __register__ = False

    def __init__(self, *args, name:str=None, session:'Session'=None, **kwargs):
        self.session = session if session is not None else self.session

        parse_key = self.__parsekey__
        name = str(id(name)) if name is None else name
        if parse_key not in self.session.extensions:
            self.session.extensions[parse_key] = {}
        if name in self.session.extensions:
            raise KeyError(f"Extension with name '{name}' aleady exists.")
        self.session.extensions[parse_key][name] = self

        self.name = name

        self.at_parse(*args, **kwargs)

    def at_parse(self):
        """This is executed when the extension instance 
        is parsed/created.

        Override for custom logic in parse time.
        """

    @classmethod
    def parse_cls(cls, d:dict, session:'Session'):
        """Parse the extension from configuration dictionary.

        Parameters
        ----------
        d : dict
            Configuration dictionary.
        session : redengine.Session
            Session object for which the extension is for.
        """
        return cls(**d, session=session)

    def delete(self):
        """Delete the extension from the session.
        
        Override for custom deletion logic."""
        del self.session.extensions[self.__parsekey__][self.name]

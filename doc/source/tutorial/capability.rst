.. BACpypes capability tutorial

Capabilities
============

The `capabilty` module is used to mix together classes that provide both
separate and overlapping functionality.  The original design was motivated
by a component architecture where collections of components that needed to be
mixed together were specified outside the application in a database.

The sample applications in this section are available in tutorial folder.
Note that you can also find them in the unit test folder as they are part of the
test suites.

Start out importing the classes in the module::

    >>> from bacpypes.capability import Capability, Collector

Transforming Data
-----------------

Assume that the application needs to transform data in a variety of different
ways, but the exact order of those functions isn't specified, but all of the
transformation functions have the same signature.

First, create a class that is going to be the foundation of the transformation
process::

    class BaseCollector(Collector):

        def transform(self, value):
            for fn in self.capability_functions('transform'):
                value = fn(self, value)

            return value

If there are no other classes mixed in, the `transform()` function doesn't
do anything::

    >>> some_transformer = BaseCollector()
    >>> some_transformer.transform(10)
    10

Adding a Transformation
-----------------------

Create a `Capability` derived class that transforms the value slightly::

    class PlusOne(Capability):

        def transform(self, value):
            return value + 1

Now create a new class that mixes in the base collector::

    class ExampleOne(BaseCollector, PlusOne):
        pass

And our transform function incorporates the new behavior::

    >>> some_transformer = ExampleOne()
    >>> some_transformer.transform(10)
    11

Add Another Transformation
--------------------------

Here is a different transformation class::

    class TimesTen(Capability):

        def transform(self, value):
            return value * 10

And the new class works as intended::

    class ExampleTwo(BaseCollector, TimesTen):
        pass

    >>> some_transformer = ExampleTwo()
    >>> some_transformer.transform(10)
    100

And the classes can be mixed in together:

    class ExampleThree(BaseCollector, PlusOne, TimesTen):
        pass

    >>> some_transformer = ExampleThree()
    >>> some_transformer.transform(10)
    110

The order of the classes makes a difference::

    class ExampleFour(BaseCollector, TimesTen, PlusOne):
        pass

    >>> some_transformer = ExampleFour()
    >>> some_transformer.transform(10)
    101


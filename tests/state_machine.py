#!/usr/bin/python

"""
Testing State Machine
---------------------
"""

try:
    # Python 3
    from queue import Queue
except ImportError:
    # Python 2
    from Queue import Queue

from bacpypes.debugging import bacpypes_debugging, ModuleLogger
from bacpypes.comm import Client, Server
from bacpypes.task import OneShotTask

from .time_machine import current_time

# some debugging
_debug = 0
_log = ModuleLogger(globals())


class Transition:

    """
    Transition
    ~~~~~~~~~~

    Instances of this class are transitions betweeen states of a state
    machine.
    """

    def __init__(self, next_state):
        self.next_state = next_state


class SendTransition(Transition):

    def __init__(self, pdu, next_state):
        Transition.__init__(self, next_state)

        self.pdu = pdu


class ReceiveTransition(Transition):

    def __init__(self, criteria, next_state):
        Transition.__init__(self, next_state)

        self.criteria = criteria


class EventTransition(Transition):

    def __init__(self, event_id, next_state):
        Transition.__init__(self, next_state)

        self.event_id = event_id


class TimeoutTransition(Transition):

    def __init__(self, timeout, next_state):
        Transition.__init__(self, next_state)

        self.timeout = timeout


class CallTransition(Transition):

    def __init__(self, fnargs, next_state):
        Transition.__init__(self, next_state)

        # a tuple of (fn, *args, *kwargs)
        self.fnargs = fnargs


#
#   match_pdu
#

@bacpypes_debugging
def match_pdu(pdu, pdu_type=None, **pdu_attrs):
    if _debug: match_pdu._debug("match_pdu %r %r %r", pdu, pdu_type, pdu_attrs)

    # check the type
    if pdu_type and not isinstance(pdu, pdu_type):
        if _debug: match_pdu._debug("    - failed match, wrong type")
        return False

    # check for matching attribute values
    for attr_name, attr_value in pdu_attrs.items():
        if not hasattr(pdu, attr_name):
            if _debug: match_pdu._debug("    - failed match, missing attr: %r", attr_name)
            return False
        if getattr(pdu, attr_name) != attr_value:
            if _debug: StateMachine._debug("    - failed match, attr value: %r, %r", attr_name, attr_value)
            return False
    if _debug: match_pdu._debug("    - successful match")

    return True


#
#   TimeoutTask
#

@bacpypes_debugging
class TimeoutTask(OneShotTask):

    def __init__(self, fn, *args, **kwargs):
        if _debug: TimeoutTask._debug("__init__ %r %r %r", fn, args, kwargs)
        OneShotTask.__init__(self)

        # save the function and args
        self.fn = fn
        self.args = args
        self.kwargs = kwargs

    def process_task(self):
        if _debug: TimeoutTask._debug("process_task %r", self.fn)
        self.fn(*self.args, **self.kwargs)

    def __repr__(self):
        return "<%s of %r at %s>" % (
            self.__class__.__name__,
            self.fn,
            hex(id(self)),
        )


#
#   State
#

@bacpypes_debugging
class State(object):

    """
    State
    ~~~~~

    Instances of this class, or a derived class, are the states of a state
    machine.
    """

    def __init__(self, state_machine, doc_string=""):
        """Create a new state, bound to a specific state machine.  This is
        typically called by the state machine.
        """
        if _debug:
            State._debug(
                "__init__ %r doc_string=%r", state_machine, doc_string
            )

        self.state_machine = state_machine
        self.doc_string = doc_string
        self.is_success_state = False
        self.is_fail_state = False

        # empty lists of send and receive transitions
        self.send_transitions = []
        self.receive_transitions = []

        # empty lists of event transitions
        self.set_event_transitions = []
        self.clear_event_transitions = []
        self.wait_event_transitions = []

        # timeout transition
        self.timeout_transition = None

        # call transition
        self.call_transition = None

    def reset(self):
        """Override this method in a derived class if the state maintains
        counters or other information.  Called when the associated state
        machine is reset.
        """
        if _debug: State._debug("reset")

    def doc(self, doc_string):
        """Change the documentation string (label) for the state.  The state
        is returned for method chaining.
        """
        if _debug: State._debug("doc %r", doc_string)

        # save the doc string
        self.doc_string = doc_string

        # chainable
        return self

    def success(self, doc_string=None):
        """Mark a state as a successful final state.  The state is returned
        for method chaining.

        :param doc_string: an optional label for the state
        """
        if _debug: State._debug("success %r", doc_string)

        # error checking
        if self.is_success_state:
            raise RuntimeError("already a success state")
        if self.is_fail_state:
            raise RuntimeError("already a fail state")

        # this is now a success state
        self.is_success_state = True

        # save the new doc string
        if doc_string is not None:
            self.doc_string = doc_string
        elif not self.doc_string:
            self.doc_string = "success"

        # chainable
        return self

    def fail(self, doc_string=None):
        """Mark a state as a failure final state.  The state is returned
        for method chaining.

        :param doc_string: an optional label for the state
        """
        if _debug: State._debug("fail %r", doc_string)

        # error checking
        if self.is_success_state:
            raise RuntimeError("already a success state")
        if self.is_fail_state:
            raise RuntimeError("already a fail state")

        # this is now a fail state
        self.is_fail_state = True

        # save the new doc string
        if doc_string is not None:
            self.doc_string = doc_string
        elif not self.doc_string:
            self.doc_string = "fail"

        # chainable
        return self

    def enter_state(self):
        """Called when the state machine is entering the state."""
        if _debug: State._debug("enter_state(%s)", self.doc_string)

        # if there is a timeout, schedule it
        if self.timeout_transition:
            if _debug: State._debug("    - waiting: %r", self.timeout_transition.timeout)

            # schedule the timeout
            self.state_machine.state_timeout_task.install_task(delta=self.timeout_transition.timeout)
        else:
            if _debug: State._debug("    - no timeout")

    def exit_state(self):
        """Called when the state machine is exiting the state."""
        if _debug: State._debug("exit_state(%s)", self.doc_string)

        # if there was a timeout, suspend it
        if self.timeout_transition:
            if _debug: State._debug("    - canceling timeout")

            self.state_machine.state_timeout_task.suspend_task()

    def send(self, pdu, next_state=None):
        """Create a SendTransition from this state to another, possibly new,
        state.  The next state is returned for method chaining.

        :param pdu: PDU to send
        :param next_state: state to transition to after sending
        """
        if _debug: State._debug("send(%s) %r next_state=%r", self.doc_string, pdu, next_state)

        # maybe build a new state
        if not next_state:
            next_state = self.state_machine.new_state()
            if _debug: State._debug("    - new next_state: %r", next_state)
        elif next_state not in self.state_machine.states:
            raise ValueError("off the rails")

        # add this to the list of transitions
        self.send_transitions.append(SendTransition(pdu, next_state))

        # return the next state
        return next_state

    def before_send(self, pdu):
        """Called before each PDU about to be sent."""
        self.state_machine.before_send(pdu)

    def after_send(self, pdu):
        """Called after each PDU sent."""
        self.state_machine.after_send(pdu)

    def receive(self, pdu_type, **pdu_attrs):
        """Create a ReceiveTransition from this state to another, possibly new,
        state.  The next state is returned for method chaining.

        :param criteria: PDU to match
        :param next_state: destination state after a successful match

        Simulate the function as if it was defined in Python3.5+ like this:
            def receive(self, *pdu_type, next_state=None, **pdu_attrs)
        """
        if _debug: State._debug("receive(%s) %r %r", self.doc_string, pdu_type, pdu_attrs)

        # extract the next_state keyword argument
        if 'next_state' in pdu_attrs:
            next_state = pdu_attrs['next_state']
            if _debug: State._debug("    - next_state: %r", next_state)

            del pdu_attrs['next_state']
        else:
            next_state = None

        # maybe build a new state
        if not next_state:
            next_state = self.state_machine.new_state()
            if _debug: State._debug("    - new next_state: %r", next_state)
        elif next_state not in self.state_machine.states:
            raise ValueError("off the rails")

        # create a bundle of the match criteria
        criteria = (pdu_type, pdu_attrs)
        if _debug: State._debug("    - criteria: %r", criteria)

        # add this to the list of transitions
        self.receive_transitions.append(ReceiveTransition(criteria, next_state))

        # return the next state
        return next_state

    def before_receive(self, pdu):
        """Called with each PDU received before matching."""
        self.state_machine.before_receive(pdu)

    def after_receive(self, pdu):
        """Called with PDU received after match."""
        self.state_machine.after_receive(pdu)

    def ignore(self, pdu_type, **pdu_attrs):
        """Create a ReceiveTransition from this state to itself, if match
        is successful the effect is to ignore the PDU.

        :param criteria: PDU to match
        """
        if _debug: State._debug("ignore(%s) %r %r", self.doc_string, pdu_type, pdu_attrs)

        # create a bundle of the match criteria
        criteria = (pdu_type, pdu_attrs)
        if _debug: State._debug("    - criteria: %r", criteria)

        # add this to the list of transitions
        self.receive_transitions.append(ReceiveTransition(criteria, self))

        # return this state, no new state is created
        return self

    def unexpected_receive(self, pdu):
        """Called with PDU that did not match.  Unless this is trapped by the
        state, the default behaviour is to fail."""
        if _debug: State._debug("unexpected_receive(%s) %r", self.doc_string, pdu)

        # pass along to the state machine
        self.state_machine.unexpected_receive(pdu)

    def set_event(self, event_id):
        """Create an EventTransition for this state that sets an event.  The
        current state is returned for method chaining.

        :param event_id: event identifier
        """
        if _debug: State._debug("set_event(%s) %r", self.doc_string, event_id)

        # add this to the list of transitions
        self.set_event_transitions.append(EventTransition(event_id, None))

        # return the next state
        return self

    def event_set(self, event_id):
        """Called with the event that was set."""
        pass

    def clear_event(self, event_id):
        """Create an EventTransition for this state that clears an event.  The
        current state is returned for method chaining.

        :param event_id: event identifier
        """
        if _debug: State._debug("clear_event(%s) %r", self.doc_string, event_id)

        # add this to the list of transitions
        self.clear_event_transitions.append(EventTransition(event_id, None))

        # return the next state
        return next_state

    def wait_event(self, event_id, next_state=None):
        """Create an EventTransition from this state to another, possibly new,
        state.  The next state is returned for method chaining.

        :param pdu: PDU to send
        :param next_state: state to transition to after sending
        """
        if _debug: State._debug("wait_event(%s) %r next_state=%r", self.doc_string, event_id, next_state)

        # maybe build a new state
        if not next_state:
            next_state = self.state_machine.new_state()
            if _debug: State._debug("    - new next_state: %r", next_state)
        elif next_state not in self.state_machine.states:
            raise ValueError("off the rails")

        # add this to the list of transitions
        self.wait_event_transitions.append(EventTransition(event_id, next_state))

        # return the next state
        return next_state

    def timeout(self, delay, next_state=None):
        """Create a TimeoutTransition from this state to another, possibly new,
        state.  There can only be one timeout transition per state.  The next
        state is returned for method chaining.

        :param delay: the amount of time to wait for a matching PDU
        :param next_state: destination state after timeout
        """
        if _debug: State._debug("timeout(%s) %r next_state=%r", self.doc_string, delay, next_state)

        # check to see if a timeout has already been specified
        if self.timeout_transition:
            raise RuntimeError("state already has a timeout")

        # maybe build a new state
        if not next_state:
            next_state = self.state_machine.new_state()
            if _debug: State._debug("    - new next_state: %r", next_state)
        elif next_state not in self.state_machine.states:
            raise ValueError("off the rails")

        # set the transition
        self.timeout_transition = TimeoutTransition(delay, next_state)

        # return the next state
        return next_state

    def call(self, fn, *args, **kwargs):
        """Create a CallTransition from this state to another, possibly new,
        state.  The next state is returned for method chaining.

        :param criteria: PDU to match
        :param next_state: destination state after a successful match

        Simulate the function as if it was defined in Python3.5+ like this:
            def receive(self, fn, *args, next_state=None, **kwargs)
        """
        if _debug: State._debug("call(%s) %r %r %r", self.doc_string, fn, args, kwargs)

        # only one call per state
        if self.call_transition:
            raise RuntimeError("only one 'call' per state")

        # extract the next_state keyword argument
        if 'next_state' in kwargs:
            next_state = kwargs['next_state']
            if _debug: State._debug("    - next_state: %r", next_state)

            del kwargs['next_state']
        else:
            next_state = None

        # maybe build a new state
        if not next_state:
            next_state = self.state_machine.new_state()
            if _debug: State._debug("    - new next_state: %r", next_state)
        elif next_state not in self.state_machine.states:
            raise ValueError("off the rails")

        # create a bundle of the match criteria
        fnargs = (fn, args, kwargs)
        if _debug: State._debug("    - fnargs: %r", fnargs)

        # add this to the list of transitions
        self.call_transition = CallTransition(fnargs, next_state)

        # return the next state
        return next_state

    def __repr__(self):
        return "<%s(%s) at %s>" % (
            self.__class__.__name__,
            self.doc_string,
            hex(id(self)),
        )


@bacpypes_debugging
class StateMachine(object):

    """
    StateMachine
    ~~~~~~~~~~~~

    A state machine consisting of states.  Every state machine has a start
    state where the state machine begins when it is started.  It also has
    an *unexpected receive* fail state where the state machine goes if
    there is an unexpected (unmatched) PDU received.
    """

    def __init__(
            self,
            timeout=None,
            start_state=None,
            unexpected_receive_state=None,
            machine_group=None,
            state_subclass=State,
            name='',
    ):
        if _debug: StateMachine._debug("__init__(%s)", name)

        # save the name for debugging
        self.name = name

        # no states to starting out, not running
        self.states = []
        self.running = False

        # flags for remembering success or fail
        self.is_success_state = None
        self.is_fail_state = None

        # might be part of a group
        self.machine_group = machine_group

        # reset to initial condition
        self.reset()

        # save the state subclass for new states
        if not issubclass(state_subclass, State):
            raise TypeError("%r is not derived from State" % (state_subclass,))
        self.state_subclass = state_subclass

        # create the start state
        if start_state:
            if start_state.state_machine:
                raise RuntimeError("start state already bound to a machine")
            self.states.append(start_state)
            start_state.state_machine = self
        else:
            start_state = self.new_state("start")
        self.start_state = start_state

        # create the unexpected receive state
        if unexpected_receive_state:
            if unexpected_receive_state.state_machine:
                raise RuntimeError("unexpected receive state already bound to a machine")
            self.states.append(unexpected_receive_state)
            unexpected_receive_state.state_machine = self
        else:
            unexpected_receive_state = self.new_state("unexpected receive").fail()
        self.unexpected_receive_state = unexpected_receive_state

        # received messages get queued during state transitions
        self.state_transitioning = 0
        self.transition_queue = Queue()

        # create a state timeout task, to be installed as necessary
        self.state_timeout_task = TimeoutTask(self.state_timeout)

        # create a state machine timeout task
        self.timeout = timeout
        if timeout:
            self.timeout_state = self.new_state("state machine timeout").fail()
            self.timeout_task = TimeoutTask(self.state_machine_timeout)
        else:
            self.timeout_state = None
            self.timeout_task = None

    def new_state(self, doc="", state_subclass=None):
        if _debug: StateMachine._debug("new_state(%s) %r %r", self.name, doc, state_subclass)

        # check for proper subclass
        if state_subclass and not issubclass(state_subclass, State):
            raise TypeError("%r is not derived from State" % (state_subclass,))

        # make the state object from the class that was provided or default
        state = (state_subclass or self.state_subclass)(self, doc)
        if _debug: StateMachine._debug("    - state: %r", state)

        # save a reference to make sure we don't go off the rails
        self.states.append(state)

        # return the new state
        return state

    def reset(self):
        if _debug: StateMachine._debug("reset(%s)", self.name)

        # make sure we're not running
        if self.running:
            raise RuntimeError("state machine running")

        # flags for remembering success or fail
        self.is_success_state = None
        self.is_fail_state = None

        # no current state, empty transaction log
        self.current_state = None
        self.transaction_log = []

        # we are not starting up
        self._startup_flag = False

        # give all the states a chance to reset
        for state in self.states:
            state.reset()

    def run(self):
        if _debug: StateMachine._debug("run(%s)", self.name)

        if self.running:
            raise RuntimeError("state machine running")
        if self.current_state:
            raise RuntimeError("not running but has a current state")

        # if there is a timeout task, schedule the fail
        if self.timeout_task:
            if _debug: StateMachine._debug("    - schedule runtime limit")
            self.timeout_task.install_task(delta=self.timeout)

        # we are starting up
        self._startup_flag = True

        # go to the start state
        self.goto_state(self.start_state)

        # startup complete
        self._startup_flag = False

        # if it is part of a group, let the group know
        if self.machine_group:
            self.machine_group.started(self)

            # if it stopped already, let the group know
            if not self.running:
                self.machine_group.stopped(self)

    def halt(self):
        """Called when the state machine should no longer be running."""
        if _debug: StateMachine._debug("halt(%s)", self.name)

        # make sure we're running
        if not self.running:
            raise RuntimeError("state machine not running")

        # cancel the timeout task
        if self.timeout_task:
            if _debug: StateMachine._debug("    - cancel runtime limit")
            self.timeout_task.suspend_task()

        # no longer running
        self.running = False

    def success(self):
        """Called when the state machine has successfully completed."""
        if _debug: StateMachine._debug("success(%s)", self.name)

        # flags for remembering success or fail
        self.is_success_state = True

    def fail(self):
        """Called when the state machine has failed."""
        if _debug: StateMachine._debug("fail(%s)", self.name)

        # flags for remembering success or fail
        self.is_fail_state = True

    def goto_state(self, state):
        if _debug: StateMachine._debug("goto_state(%s) %r", self.name, state)

        # where do you think you're going?
        if state not in self.states:
            raise RuntimeError("off the rails")

        # transitioning
        self.state_transitioning += 1

        # exit the old state
        if self.current_state:
            self.current_state.exit_state()
        elif state is self.start_state:
            # starting up
            self.running = True
        else:
            raise RuntimeError("start at the start state")

        # here we are
        current_state = self.current_state = state

        # let the state do something
        current_state.enter_state()
        if _debug: StateMachine._debug("    - state entered")

        # events are managed by a state machine group
        if self.machine_group:
            # setting events
            for transition in current_state.set_event_transitions:
                if _debug: StateMachine._debug("    - setting event: %r", transition.event_id)
                self.machine_group.set_event(transition.event_id)

            # clearing events
            for transition in current_state.clear_event_transitions:
                if _debug: StateMachine._debug("    - clearing event: %r", transition.event_id)
                self.machine_group.clear_event(transition.event_id)

        # check for success state
        if current_state.is_success_state:
            if _debug: StateMachine._debug("    - success state")
            self.state_transitioning -= 1

            self.halt()
            self.success()

            # if it is part of a group, let the group know
            if self.machine_group and not self._startup_flag:
                self.machine_group.stopped(self)

            return

        # check for fail state
        if current_state.is_fail_state:
            if _debug: StateMachine._debug("    - fail state")
            self.state_transitioning -= 1

            self.halt()
            self.fail()

            # if it is part of a group, let the group know
            if self.machine_group and not self._startup_flag:
                self.machine_group.stopped(self)

            return

        # assume we can stay
        next_state = None

        # events are managed by a state machine group
        if self.machine_group:
            # check to see if there are events that are already set
            for transition in current_state.wait_event_transitions:
                if _debug: StateMachine._debug("    - waiting event: %r", transition.event_id)

                # check for a transition
                if transition.event_id in self.machine_group.events:
                    next_state = transition.next_state
                    if _debug: StateMachine._debug("    - next_state: %r", next_state)

                    if next_state is not current_state:
                        break
            else:
                if _debug: StateMachine._debug("    - no events already set")
        else:
            if _debug: StateMachine._debug("    - not part of a group")

        # call things that need to be called
        if current_state.call_transition:
            if _debug: StateMachine._debug("    - calling: %r", current_state.call_transition)

            # pull apart the pieces and call it
            fn, args, kwargs = current_state.call_transition.fnargs
            try:
                fn( *args, **kwargs)
                if _debug: StateMachine._debug("    - called, no exception")

                # check for a transition
                next_state = current_state.call_transition.next_state
                if _debug: StateMachine._debug("    - next_state: %r", next_state)

            except AssertionError as err:
                if _debug: StateMachine._debug("    - called, exception: %r", err)
                self.state_transitioning -= 1

                self.halt()
                self.fail()

                # if it is part of a group, let the group know
                if self.machine_group and not self._startup_flag:
                    self.machine_group.stopped(self)

                return
        else:
            if _debug: StateMachine._debug("    - no calls")

        # send everything that needs to be sent
        if not next_state:
            for transition in current_state.send_transitions:
                if _debug: StateMachine._debug("    - sending: %r", transition)

                current_state.before_send(transition.pdu)
                self.send(transition.pdu)
                current_state.after_send(transition.pdu)

                # check for a transition
                next_state = transition.next_state
                if _debug: StateMachine._debug("    - next_state: %r", next_state)

                if next_state is not current_state:
                    break

        if not next_state:
            if _debug: StateMachine._debug("    - nowhere to go")

        elif next_state is self.current_state:
            if _debug: StateMachine._debug("    - going nowhere")

        else:
            if _debug: StateMachine._debug("    - going")

            self.goto_state(next_state)

        # no longer transitioning
        self.state_transitioning -= 1

        # could be recursive call
        if not self.state_transitioning:
            while self.running and not self.transition_queue.empty():
                pdu = self.transition_queue.get()
                if _debug: StateMachine._debug("    - pdu: %r", pdu)

                # try again
                self.receive(pdu)

    def before_send(self, pdu):
        """Called before each PDU about to be sent."""

        # add a reference to the pdu in the transaction log
        self.transaction_log.append(("<<<", pdu),)

    def send(self, pdu):
        raise NotImplementedError("send not implemented")

    def after_send(self, pdu):
        """Called after each PDU sent."""
        pass

    def before_receive(self, pdu):
        """Called with each PDU received before matching."""

        # add a reference to the pdu in the transaction log
        self.transaction_log.append((">>>", pdu),)

    def receive(self, pdu):
        if _debug: StateMachine._debug("receive(%s) %r", self.name, pdu)

        # check to see if haven't started yet or we are transitioning
        if (not self.current_state) or self.state_transitioning:
            if _debug: StateMachine._debug("    - queue for later")

            self.transition_queue.put(pdu)
            return

        # if this is not running it already completed
        if not self.running:
            if _debug: StateMachine._debug("    - already completed")
            return

        # reference the current state
        current_state = self.current_state
        if _debug: StateMachine._debug("    - current_state: %r", current_state)

        # let the state know this was received
        current_state.before_receive(pdu)

        match_found = False

        # look for a matching receive transition
        for transition in current_state.receive_transitions:
            if self.match_pdu(pdu, transition.criteria):
                if _debug: StateMachine._debug("    - match found")
                match_found = True

                # let the state know this was matched
                current_state.after_receive(pdu)

                # check for a transition
                next_state = transition.next_state
                if _debug: StateMachine._debug("    - next_state: %r", next_state)

                # a match was found, but by transitioning back to the
                # current state, the pdu will not be "unexpectedly received"
                # and there could be a subsequent match
                if next_state is not current_state:
                    break
        else:
            if _debug: StateMachine._debug("    - no matches")

        if not match_found:
            if _debug: StateMachine._debug("    - unexpected")
            current_state.unexpected_receive(pdu)

        elif next_state is not current_state:
            if _debug: StateMachine._debug("    - going")

            self.goto_state(next_state)

    def after_receive(self, pdu):
        """Called with PDU received after match."""
        pass

    def unexpected_receive(self, pdu):
        """Called with PDU that did not match.  Unless this is trapped by the
        state, the default behaviour is to fail."""
        if _debug: StateMachine._debug("unexpected_receive(%s) %r", self.name, pdu)

        # go to the unexpected receive state (failing)
        self.goto_state(self.unexpected_receive_state)

    def event_set(self, event_id):
        """Called by the state machine group when an event is set, the state
        machine checks to see if it's waiting for the event and makes the
        state transition if there is a match."""
        if _debug: StateMachine._debug("event_set(%s) %r", self.name, event_id)

        if not self.running:
            if _debug: StateMachine._debug("    - not running")
            return

        # check to see if we are transitioning
        if self.state_transitioning:
            if _debug: StateMachine._debug("    - transitioning")
            return
        if not self.current_state:
            raise RuntimeError("no current state")
        current_state = self.current_state

        match_found = False

        # look for a matching event transition
        for transition in current_state.wait_event_transitions:
            if transition.event_id == event_id:
                if _debug: StateMachine._debug("    - match found")
                match_found = True

                # let the state know this event was set
                current_state.event_set(event_id)

                # check for a transition
                next_state = transition.next_state
                if _debug: StateMachine._debug("    - next_state: %r", next_state)

                if next_state is not current_state:
                    break
        else:
            if _debug: StateMachine._debug("    - going nowhere")

        if match_found and next_state is not current_state:
            if _debug: StateMachine._debug("    - going")

            self.goto_state(next_state)

    def state_timeout(self):
        if _debug: StateMachine._debug("state_timeout(%s)", self.name)

        if not self.running:
            raise RuntimeError("state machine not running")
        if not self.current_state.timeout_transition:
            raise RuntimeError("state timeout, but no timeout transition")

        # go to the state specified
        self.goto_state(self.current_state.timeout_transition.next_state)

    def state_machine_timeout(self):
        if _debug: StateMachine._debug("state_machine_timeout(%s)", self.name)

        if not self.running:
            raise RuntimeError("state machine not running")

        # go to the state specified
        self.goto_state(self.timeout_state)

    def match_pdu(self, pdu, criteria):
        if _debug: StateMachine._debug("match_pdu(%s) %r %r", self.name, pdu, criteria)

        # separate the pdu_type and attributes to match
        pdu_type, pdu_attrs = criteria

        # pass along to the global function
        return match_pdu(pdu, pdu_type, **pdu_attrs)

    def __repr__(self):
        if not self.current_state:
            state_text = "not started"
        elif self.is_success_state:
            state_text = "success"
        elif self.is_fail_state:
            state_text = "fail"
        elif not self.running:
            state_text = "idle"
        else:
            state_text = "in"

        if self.current_state:
            state_text += " " + repr(self.current_state)

        return "<%s(%s) %s at %s>" % (
            self.__class__.__name__,
            self.name,
            state_text,
            hex(id(self)),
            )


@bacpypes_debugging
class StateMachineGroup(object):

    """
    StateMachineGroup
    ~~~~~~~~~~~~~~~~~

    A state machine group is a collection of state machines that are all
    started and stopped together.  There are methods available to derived
    classes that are called when all of the machines in the group have
    completed, either all successfully or at least one has failed.

    .. note:: When creating a group of state machines, add the ones that
        are expecting to receive one or more PDU's first before the ones
        that send PDU's.  They will be started first, and be ready for the
        PDU that might be sent.
    """

    def __init__(self):
        """Create a state machine group."""
        if _debug: StateMachineGroup._debug("__init__")

        # empty list of machines
        self.state_machines = []

        # flag for starting up
        self._startup_flag = False

        # flag for at least one machine running
        self.is_running = False

        # flags for remembering success or fail
        self.is_success_state = None
        self.is_fail_state = None

        # set of events that are set
        self.events = set()

    def append(self, state_machine):
        """Add a state machine to the end of the list of state machines."""
        if _debug: StateMachineGroup._debug("append %r", state_machine)

        # check the state machine
        if not isinstance(state_machine, StateMachine):
            raise TypeError("not a state machine")
        if state_machine.machine_group:
            raise RuntimeError("state machine already a part of a group")

        # tell the state machine it is a member of this group
        state_machine.machine_group = self

        # add it to the list
        self.state_machines.append(state_machine)

    def remove(self, state_machine):
        """Remove a state machine from the list of state machines."""
        if _debug: StateMachineGroup._debug("remove %r", state_machine)

        # check the state machine
        if not isinstance(state_machine, StateMachine):
            raise TypeError("not a state machine")
        if state_machine.machine_group is not self:
            raise RuntimeError("state machine not a member of this group")

        # tell the state machine it is no longer a member of this group
        state_machine.machine_group = None

        # pass along to the list
        self.state_machines.remove(state_machine)

    def reset(self):
        """Resets all the machines in the group."""
        if _debug: StateMachineGroup._debug("reset")

        # pass along to each machine
        for state_machine in self.state_machines:
            if _debug: StateMachineGroup._debug("    - resetting: %r", state_machine)
            state_machine.reset()

        # flags for remembering success or fail
        self.is_success_state = False
        self.is_fail_state = False

        # events that are set
        self.events = set()

    def set_event(self, event_id):
        """Save an event as 'set' and pass it to the state machines to see
        if they are in a state that is waiting for the event."""
        if _debug: StateMachineGroup._debug("set_event %r", event_id)

        self.events.add(event_id)
        if _debug: StateMachineGroup._debug("    - event set")

        # pass along to each machine
        for state_machine in self.state_machines:
            if _debug: StateMachineGroup._debug("    - state_machine: %r", state_machine)
            state_machine.event_set(event_id)

    def clear_event(self, event_id):
        """Remove an event from the set of elements that are 'set'."""
        if _debug: StateMachineGroup._debug("clear_event %r", event_id)

        if event_id in self.events:
            self.events.remove(event_id)
            if _debug: StateMachineGroup._debug("    - event cleared")
        else:
            if _debug: StateMachineGroup._debug("    - noop")

    def run(self):
        """Runs all the machines in the group."""
        if _debug: StateMachineGroup._debug("run")

        # turn on the startup flag
        self._startup_flag = True
        self.is_running = True

        # pass along to each machine
        for state_machine in self.state_machines:
            if _debug: StateMachineGroup._debug("    - starting: %r", state_machine)
            state_machine.run()

        # turn off the startup flag
        self._startup_flag = False
        if _debug: StateMachineGroup._debug("    - all started")

        # check for success/fail, all of the machines may already be done
        all_success, some_failed = self.check_for_success()
        if all_success:
            self.success()
        elif some_failed:
            self.fail()
        else:
            if _debug: StateMachineGroup._debug("    - some still running")

    def started(self, state_machine):
        """Called by a state machine in the group when it has completed its
        transition into its starting state."""
        if _debug: StateMachineGroup._debug("started %r", state_machine)

    def stopped(self, state_machine):
        """Called by a state machine after it has halted and its success()
        or fail() method has been called."""
        if _debug: StateMachineGroup._debug("stopped %r", state_machine)

        # if we are starting up try again later
        if self._startup_flag:
            if _debug: StateMachineGroup._debug("    - still starting up")
            return

        all_success, some_failed = self.check_for_success()
        if all_success:
            self.success()
        elif some_failed:
            self.fail()
        else:
            if _debug: StateMachineGroup._debug("    - some still running")

    def check_for_success(self):
        """Called after all of the machines have started, and each time a
        machine has stopped, to see if the entire group should be considered
        a success or fail."""
        if _debug: StateMachineGroup._debug("check_for_success")

        # accumulators
        all_success = True
        some_failed = False

        # check each machine
        for state_machine in self.state_machines:
            if state_machine.running:
                if _debug: StateMachineGroup._debug("    - running: %r", state_machine)
                all_success = some_failed = None
                break

            # if there is no current state it hasn't started
            if not state_machine.current_state:
                if _debug: StateMachineGroup._debug("    - not started: %r", state_machine)
                all_success = some_failed = None
                continue

            all_success = all_success and state_machine.current_state.is_success_state
            some_failed = some_failed or state_machine.current_state.is_fail_state

        if _debug:
            StateMachineGroup._debug("    - all_success: %r", all_success)
            StateMachineGroup._debug("    - some_failed: %r", some_failed)

        # return the results of the check
        return (all_success, some_failed)

    def halt(self):
        """Halts all of the running machines in the group."""
        if _debug: StateMachineGroup._debug("halt")

        # pass along to each machine
        for state_machine in self.state_machines:
            if state_machine.running:
                state_machine.halt()

    def success(self):
        """Called when all of the machines in the group have halted and they
        are all in a 'success' final state."""
        if _debug: StateMachineGroup._debug("success")

        self.is_running = False
        self.is_success_state = True

    def fail(self):
        """Called when all of the machines in the group have halted and at
        at least one of them is in a 'fail' final state."""
        if _debug:
            StateMachineGroup._debug("fail")
            for state_machine in self.state_machines:
                StateMachineGroup._debug("    - machine: %r", state_machine)
                for direction, pdu in state_machine.transaction_log:
                    StateMachineGroup._debug("        %s %s", direction, str(pdu))

        self.is_running = False
        self.is_fail_state = True


@bacpypes_debugging
class ClientStateMachine(Client, StateMachine):

    """
    ClientStateMachine
    ~~~~~~~~~~~~~~~~~~

    An instance of this class sits at the top of a stack.  PDU's that the
    state machine sends are sent down the stack and PDU's coming up the
    stack are fed as received PDU's.
    """

    def __init__(self, name=''):
        if _debug: ClientStateMachine._debug("__init__")

        Client.__init__(self)
        StateMachine.__init__(self, name=name)

    def send(self, pdu):
        if _debug: ClientStateMachine._debug("send(%s) %r", self.name, pdu)
        self.request(pdu)

    def confirmation(self, pdu):
        if _debug: ClientStateMachine._debug("confirmation(%s) %r", self.name, pdu)
        self.receive(pdu)


@bacpypes_debugging
class ServerStateMachine(Server, StateMachine):

    """
    ServerStateMachine
    ~~~~~~~~~~~~~~~~~~

    An instance of this class sits at the bottom of a stack.  PDU's that the
    state machine sends are sent up the stack and PDU's coming down the
    stack are fed as received PDU's.
    """

    def __init__(self, name=''):
        if _debug: ServerStateMachine._debug("__init__")

        Server.__init__(self)
        StateMachine.__init__(self, name=name)

    def send(self, pdu):
        if _debug: ServerStateMachine._debug("send %r", pdu)
        self.response(pdu)

    def indication(self, pdu):
        if _debug: ServerStateMachine._debug("indication %r", pdu)
        self.receive(pdu)


#
#   TrafficLog
#

class TrafficLog:

    def __init__(self):
        """Initialize with no traffic."""
        self.traffic = []

    def __call__(self, *args):
        """Capture the current time and the arguments."""
        self.traffic.append((current_time(),) + args)

    def dump(self, handler_fn):
        """Dump the traffic, pass the correct handler like SomeClass._debug"""
        for args in self.traffic:
            arg_format = "   %6.3f:"
            for arg in args[1:]:
                if hasattr(arg, 'debug_contents'):
                    arg_format += " %r"
                else:
                    arg_format += " %s"
            handler_fn(arg_format, *args)


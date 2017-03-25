.. BACpypes change of value services

Change of Value (COV) Services
==============================

.. class:: ChangeOfValueServices(Capability)

    This class provides the capability of managing COV subscriptions and
    initiating COV notifications.

    .. method:: do_SubscribeCOVRequest(apdu):

        :param SubscribeCOVRequest apdu: request from the network

        This method processes the request by looking up the referenced object
        and attaching a COV detection algorithm object.  Any changes the to
        referenced object properties (such as *presentValue* to *statusFlags*)
        will trigger the algorithm to run and initiate COV notifications as
        necessary.

    .. method:: add_subscription(cov)

        This method adds a subscription to the internal dictionary of subscriptions
        indexed by the object reference.  There can be multiple COV subscriptions
        for the same object.

    .. method:: cancel_subscription(cov)

        This method removes a subscription from the internal dictionary of
        subscriptions.  If all of the subscriptinos have been removed, for
        example they have all expired, then the detection "hook" into the
        object is removed.

    .. method:: cov_notification(cov, request)

        This method is used to wrap a COV notification request in an
        IOCB wrapper, submitting it as an IO request.  The following confirmation
        function will be called when it is complete.

    .. method:: cov_confirmation(iocb)

        This method looks at the response that was given to the COV notification
        and dispatchs one of the following functions.

    .. method:: cov_ack(cov, request, response)

        This method is called when the client has responded with a simple
        acknowledgement.

    .. method:: cov_error(cov, request, response)

        This method is called when the client has responded with an error.
        Depending on the error, the COV subscription might be canceled.

    .. method:: cov_reject(cov, request, response)

        This method is called when the client has responded with a reject.
        Depending on the error, the COV subscription might be canceled.

    .. method:: cov_abort(cov, request, response)

        This method is called when the client has responded with an abort.
        Depending on the error, the COV subscription might be canceled.


Support Classes
---------------

.. class:: ActiveCOVSubscriptions(Property)

    An instance of this property is added to the local device object.  When
    the property is read it will return a list of COVSubscription objects.


.. class:: SubscriptionList

    .. method:: append(cov)

        :param Subscription cov: additional subscription

    .. method:: remove(cov)

        :param Subscription cov: subscription to remove

    .. method:: find(client_addr, proc_id, obj_id)

        :param Address client_addr: client address
        :param int proc_id: client process identifier
        :param ObjectIdentifier obj_id: object identifier

        This method finds a matching Subscription object where all three
        parameters match.  It is used when a subscription request arrives
        it is used to determine if it should be renewed or canceled.

.. class:: Subscription(OneShotTask)

    Instances of this class are active subscriptions with a lifetime.  When the
    subscription is created it "installs" itself as a task for the end of its
    lifetime and when the process_task function is called the subscription
    is canceled.

    .. method:: __init__(obj_ref, client_addr, proc_id, obj_id, confirmed, lifetime)

        :param obj_ref: reference to the object being monitored
        :param client_addr: address of the client
        :param proc_id: process id of the client
        :param obj_id: object identifier
        :param confirmed: issue confirmed notifications
        :param lifetime: subscription lifetime

    .. method:: cancel_subscription()

        This method is called to cancel a subscription, it is called by
        process_task.

    .. method:: renew_subscription(lifetime)

        :param int lifetime: seconds until expiration

        This method is called to renew a subscription.

    .. method:: process_task()

        Call when the lifetime of the subscription has run out.

.. class:: COVDetection(DetectionAlgorithm)

    This is a base class for a series of COV detection algorithms.  The derived
    classes provide a list of the properties that are being monitored for
    changes and a list of properties that are reported.

    .. method:: execute()

        This method overrides the execute function of the detection algorithm.

    .. method:: send_cov_notifications()

        This method sends out notifications to all of the subscriptions
        that are associated with the algorithm.

.. class:: GenericCriteria(COVDetection)

    This is the simplest detection algorithm that monitors the present value
    and status flags of an object.

.. class:: COVIncrementCriteria(COVDetection)

    This detection algorithm is used for those objects that have a COV increment
    property, such as Analog Value Objects, where the change in the present
    value needs to exceed some delta value.

.. class:: AccessDoorCriteria(COVDetection)

    This detection algorithm is used for Access Door Objects.

.. class:: AccessPointCriteria(COVDetection)

    This detection algorithm is used for Access Point Objects.

.. class:: CredentialDataInputCriteria(COVDetection)

    This detection algorithm is used for Credential Data Input Objects.

.. class:: LoadControlCriteria(COVDetection)

    This detection algorithm is used for Load Control Objects.

.. class:: PulseConverterCriteria(COVDetection)

    This detection algorithm is used for Pulse Converter Objects.

#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" Package for specifying Services

In daedalus, a service is not a ``microservice``.
Instead, it is a standalone process with a definite
life-cycle to perform a certain function.

Life Cycle of a Service
=======================

A service has the following life cycles
* CREATED
* INITIALIZING
* READY
* ACTIVE
* INACTIVE
* TERMINATING
* STOPPED

Creating a Service
==================

Running a Service
=================

Communicating with a Service
============================

Shutting down a Service
=======================

There are 2 ways to shut down a service.
* First way is to send a TERM signal via Ctrl-C
* Second approach is to call it's endpoint to
    shut down the service

Both ways, the service will go into the ``TERMINATING``
state in order to clean its internal data structure,
save whatever state etc before finally exiting.

Note:
-----

As per any other regular Python thread processes, interrupting them
is not a straight foward task, so care needs to be taken when
adding new tasks to the event loop, i.e. one cannot have an endless
loop without polling for the exit flog. Otherwise this will lead
to the service not being able to shut down properly.


"""

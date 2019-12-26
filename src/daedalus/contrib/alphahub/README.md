Alphahub API query specification

1. A basic query comprises a dictionary with 3 keys:

```python
{
    'namespace' : 'alpha',
    'select' : { ... },
    'filter' : { ... }, 
    'option' : { ... },
}
```

Examples
========

Before we define the rules of Alphahub API, we first use some illustrations 
to crystallize what are the functionilities we would like to incorporate 
into the query itself. 

Note that we do not aim to cover the entirety of the SQL language as it is 
too rich, but as long as we are able to express the most common functionalities,
it would be good enough.

Simple Query
------------

At the most basic level, a user should be able to simply express the fields that he want 
to retrieve given a simple set of filter conditions:

```python
{
    'namespace': 'alpha',
    'select': ['id', 'name', 'status'],
    'filter': {
        'status' : 'PROD',
        'instruments' : 'equity',
        'region' : ['USA', 'JPN'],
        'delay' : '1',
    },
    'option': {
        'limit' : 100,
    },
}
```

* namespace: Since we are dealing with different levels of Alphas, we use namespace to denote them, i.e. 'alpha', 'batch', 'meta'

* In the most basic specification, if it is just key-value, then it is assumed to be key = value clause, and if it is key-list_of_value pair, then it will
    be key in [list of clause]

For a more complicated example, suppose instead of equality, the user wants to compare using some other operators like '$gt', '$lt', '$ge', '$le', '$in', '$nin', '$between'
The query would look something like this.

```python
{
    'namespace': 'alpha',
    'select': ['id', 'name', 'status'],
    'filter': {
        'birthday' : { 
            '$gt' : 'PROD'
        },
        'instruments' : {
            '$in' : ['equity', 'fx'],
        },
        'region' : 'USA',
        'delay' : '1',
    },
    'aggregate' : {
        '$group': 
    }
    'option': {
        'limit' : 100,
    },
}
```

Specification
=============

Filter
------

* The most basic query condition can be written as below. This is implicitly the equality operator
 
{field: value, ...}

* For membership query, this can be written as

{field: [value,], ...}

* In some cases whereby the operator is not equality or membership, it can be written as

field: {binary-operator: value }
field: {ternary-operator: [value1, value2]}
field: {list-operator: [value1,]}

Note: The two short form above is then equaivalent to:

field: {'$eq': value}
field: {'$in': [values,]}

For each condition, it can also be an operator query, i.e.

binary-operator: [field, value]
ternary-operator: [field, value1, value2]
list-operator: [field, value1,...]

* For logical operator

'$or': [condition1, condition2,]
'$and': [condition1, condition2,]

* At this point of time I think we will not support expression, though if we need to we can denote field name by '?fieldname' (it can be $ or ?. Mongo uses $ and couchbase uses ?) to distinguish it from value

* A field condition is then defined by the following:


Select
------

* The select clause allows us to specify what to show. If nothing is specified, then only the Alpha ID will be displayed.

* If it is a list of field names, then we simply show the field names

select: ['id', 'name', 'status']

* For some fields, there are additional options, then we use a dictionary to denote the option

select: {
    'id': 1,
    'name': 1,
    'test.Bias': 'simple',
}


Aggregate
---------

* These are additional aggregate functions such as '$group'

{ '$group' : ['$field', ...] }

Option
------

* These are additional optional clauses to control the output

* Some of the known options are:

** 'limit' : 100
** 'page' : 3
** 'order' : {field: [1|-1],... }


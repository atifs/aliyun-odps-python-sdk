#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

from odps.tests.core import TestBase, to_str
from odps.compat import unittest
from odps.models import Schema
from odps.df.expr.expressions import CollectionExpr
from odps.df.types import validate_data_type
from odps.df.expr.tests.core import MockTable


EXPECTED_PROJECTION_FORMAT = '''\
Collection: ref_0
  odps.Table
    name: mocked_project.`pyodps_test_expr_table`
    schema:
      name    : string
      id      : int64

Collection: ref_1
  Projection[collection]
    collection: ref_0
    selections:
      name = Column[sequence(string)] 'name' from collection ref_0
      new_id = Column[sequence(int64)] 'id' from collection ref_0

new_id = TypedSequence[sequence(float32)]
  new_id = Column[sequence(int64)] 'new_id' from collection ref_1
'''

EXPECTED_FILTER_FORMAT = '''\
Collection: ref_0
  odps.Table
    name: mocked_project.`pyodps_test_expr_table`
    schema:
      name    : string
      id      : int64

Filter[collection]
  collection: ref_0
  predicate:
    And[sequence(boolean)]
      NotEqual[sequence(boolean)]
        name = Column[sequence(string)] 'name' from collection ref_0
        Scalar[string]
          'test'
      Greater[sequence(boolean)]
        id = Column[sequence(int64)] 'id' from collection ref_0
        Scalar[int8]
          100
'''

EXPECTED_SLICE_FORMAT = '''\
Collection: ref_0
  odps.Table
    name: mocked_project.`pyodps_test_expr_table`
    schema:
      name    : string
      id      : int64

Slice[collection]
  collection: ref_0
  stop:
    Scalar[int8]
      100
'''

EXPECTED_SLICE_WITH_START_STEP_FORMAT = '''\
Collection: ref_0
  odps.Table
    name: mocked_project.`pyodps_test_expr_table`
    schema:
      name    : string
      id      : int64

Slice[collection]
  collection: ref_0
  start:
    Scalar[int8]
      5
  stop:
    Scalar[int8]
      100
  step:
    Scalar[int8]
      3
'''

EXPECTED_ARITHMETIC_FORMAT = '''\
Collection: ref_0
  odps.Table
    name: mocked_project.`pyodps_test_expr_table`
    schema:
      name    : string
      id      : int64

Add[sequence(float64)]
  Add[sequence(float64)]
    Substract[sequence(float64)]
      Add[sequence(float64)]
        Substract[sequence(float64)]
          Add[sequence(float64)]
            Negate[sequence(int64)]
              id = Column[sequence(int64)] 'id' from collection ref_0
            Scalar[float64]
              20.34
          id = Column[sequence(int64)] 'id' from collection ref_0
        Multiply[sequence(float64)]
          Scalar[float64]
            20.0
          id = Column[sequence(int64)] 'id' from collection ref_0
      Divide[sequence(float64)]
        id = Column[sequence(int64)] 'id' from collection ref_0
        Scalar[float64]
          4.9
    Scalar[int8]
      20
  FloorDivide[sequence(float64)]
    id = Column[sequence(int64)] 'id' from collection ref_0
    Scalar[float64]
      1.2
'''

EXPECTED_SORT_FORMAT = '''\
Collection: ref_0
  odps.Table
    name: mocked_project.`pyodps_test_expr_table`
    schema:
      name    : string
      id      : int64

SortBy[collection]
  collection: ref_0
  keys:
    SortKey
      by
        name = Column[sequence(string)] 'name' from collection ref_0
      ascending
        True
    SortKey
      by
        id = Column[sequence(int64)] 'id' from collection ref_0
      ascending
        False
'''

EXPECTED_DISTINCT_FORMAT = '''\
Collection: ref_0
  odps.Table
    name: mocked_project.`pyodps_test_expr_table`
    schema:
      name    : string
      id      : int64

Distinct[collection]
  collection: ref_0
  distinct:
    name = Column[sequence(string)] 'name' from collection ref_0
    Add[sequence(int64)]
      id = Column[sequence(int64)] 'id' from collection ref_0
      Scalar[int8]
        1
'''


EXPECTED_GROUPBY_FORMAT = '''\
Collection: ref_0
  odps.Table
    name: mocked_project.`pyodps_test_expr_table`
    schema:
      name    : string
      id      : int64

GroupBy[collection]
  collection: ref_0
  by:
    name = Column[sequence(string)] 'name' from collection ref_0
    id = Column[sequence(int64)] 'id' from collection ref_0
  aggregations:
    new_id = sum[sequence(int64)]
      id = Column[sequence(int64)] 'id' from collection ref_0
'''


EXPECTED_GROUPBY_COUNT_FORMAT = '''\
Collection: ref_0
  odps.Table
    name: mocked_project.`pyodps_test_expr_table`
    schema:
      name    : string
      id      : int64

GroupBy[collection]
  collection: ref_0
  by:
    name = Column[sequence(string)] 'name' from collection ref_0
    id = Column[sequence(int64)] 'id' from collection ref_0
  aggregations:
    count = count[sequence(int64)]
      collection: ref_0
'''


EXPECTED_MUTATE_FORMAT = '''\
Collection: ref_0
  odps.Table
    name: mocked_project.`pyodps_test_expr_table`
    schema:
      name    : string
      id      : int64

Mutate[collection]
  collection: ref_0
  by:
    name = Column[sequence(string)] 'name' from collection ref_0
  mutates:
    RowNumber[sequence(int64)]
      PartitionBy:
        name = Column[sequence(string)] 'name' from collection ref_0
'''


EXPECTED_REDUCTION_FORMAT = '''\
Collection: ref_0
  odps.Table
    name: mocked_project.`pyodps_test_expr_table`
    schema:
      name    : string
      id      : int64

Collection: ref_1
  GroupBy[collection]
    collection: ref_0
    by:
      id = Column[sequence(int64)] 'id' from collection ref_0
    aggregations:
      id_std = std[sequence(float64)]
        id = Column[sequence(int64)] 'id' from collection ref_0

id_std = Column[sequence(float64)] 'id_std' from collection ref_1
'''


EXPECTED_REDUCTION_FORMAT2 = '''\
Collection: ref_0
  odps.Table
    name: mocked_project.`pyodps_test_expr_table`
    schema:
      name    : string
      id      : int64

mean = Mean[float64]
  id = Column[sequence(int64)] 'id' from collection ref_0
'''


EXPECTED_REDUCTION_FORMAT3 = '''\
Collection: ref_0
  odps.Table
    name: mocked_project.`pyodps_test_expr_table`
    schema:
      name    : string
      id      : int64

count = Count[int64]
  collection: ref_0
'''


EXPECTED_WINDOW_FORMAT1 = '''\
Collection: ref_0
  odps.Table
    name: mocked_project.`pyodps_test_expr_table`
    schema:
      name    : string
      id      : int64

rank = Rank[sequence(int64)]
  PartitionBy:
    name = Column[sequence(string)] 'name' from collection ref_0
  OrderBy:
    SortKey
      by
        id = Column[sequence(int64)] 'id' from collection ref_0
      ascending
        False
'''

EXPECTED_WINDOW_FORMAT2 = '''\
Collection: ref_0
  odps.Table
    name: mocked_project.`pyodps_test_expr_table`
    schema:
      name    : string
      id      : int64

id_mean = CumMean[sequence(float64)]
  id = Column[sequence(int64)] 'id' from collection ref_0
  PartitionBy:
    id = Column[sequence(int64)] 'id' from collection ref_0
  distinct:
    Scalar[boolean]
      True
  preceding:
    Scalar[int8]
      10
  following:
    Scalar[int8]
      5
'''

EXPECTED_STRING_FORMAT = '''\
Collection: ref_0
  odps.Table
    name: mocked_project.`pyodps_test_expr_table`
    schema:
      name    : string
      id      : int64

name = Contains[sequence(boolean)]
  name = Column[sequence(string)] 'name' from collection ref_0
  pat:
    Scalar[string]
      'test'
  case:
    Scalar[boolean]
      True
  flags:
    Scalar[int8]
      0
  regex:
    Scalar[boolean]
      True
'''

EXPECTED_ELEMENT_FORMAT = '''\
Collection: ref_0
  odps.Table
    name: mocked_project.`pyodps_test_expr_table`
    schema:
      name    : string
      id      : int64

id = Between[sequence(boolean)]
  id = Column[sequence(int64)] 'id' from collection ref_0
  left:
    Scalar[int8]
      1
  right:
    Scalar[int8]
      3
  inclusive:
    Scalar[boolean]
      True
'''

EXPECTED_DATETIME_FORMAT = '''\
Collection: ref_0
  odps.Table
    name: mocked_project.`pyodps_test_expr_table`
    schema:
      name    : string
      id      : int64

name = Strftime[sequence(string)]
  TypedSequence[sequence(datetime)]
    name = Column[sequence(string)] 'name' from collection ref_0
  date_format:
    Scalar[string]
      '%Y'
'''

EXPECTED_SWITCH_FORMAT = '''\
Collection: ref_0
  odps.Table
    name: mocked_project.`pyodps_test_expr_table`
    schema:
      name    : string
      id      : int64

Switch[sequence(string)]
  case:
    id = Column[sequence(int64)] 'id' from collection ref_0
  when:
    Scalar[int8]
      3
  then:
    name = Column[sequence(string)] 'name' from collection ref_0
  when:
    Scalar[int8]
      4
  then:
    Add[sequence(string)]
      name = Column[sequence(string)] 'name' from collection ref_0
      Scalar[string]
        'abc'
  default:
    Add[sequence(string)]
      name = Column[sequence(string)] 'name' from collection ref_0
      Scalar[string]
        'test'
'''


EXPECTED_JOIN_FORMAT = '''\
Collection: ref_0
  odps.Table
    name: mocked_project.`pyodps_test_expr_table`
    schema:
      name    : string
      id      : int64

Collection: ref_1
  odps.Table
    name: mocked_project.`pyodps_test_expr_table2`
    schema:
      name2     : string
      id2       : int64

InnerJoin[collection]
  collection(left): ref_0
  collection(right): ref_1
  on:
    Equal[sequence(boolean)]
      name = Column[sequence(string)] 'name' from collection ref_0
      name2 = Column[sequence(string)] 'name2' from collection ref_1
'''


EXPECTED_CAST_FORMAT = '''\
Collection: ref_0
  odps.Table
    name: mocked_project.`pyodps_test_expr_table`
    schema:
      name    : string
      id      : int64

id = TypedSequence[sequence(float64)]
  id = Column[sequence(int64)] 'id' from collection ref_0
'''


class Test(TestBase):
    def setup(self):
        datatypes = lambda *types: [validate_data_type(t) for t in types]
        schema = Schema.from_lists(['name', 'id'], datatypes('string', 'int64'))
        table = MockTable(name='pyodps_test_expr_table', schema=schema)

        self.expr = CollectionExpr(_source_data=table, _schema=schema)

        schema2 = Schema.from_lists(['name2', 'id2'], datatypes('string', 'int64'))
        table2 = MockTable(name='pyodps_test_expr_table2', schema=schema2)
        self.expr2 = CollectionExpr(_source_data=table2, _schema=schema2)

    def _lines_eq(self, expected, actual):
        self.assertSequenceEqual([to_str(line.rstrip()) for line in expected.split('\n')],
                                 [to_str(line.rstrip()) for line in actual.split('\n')])

    def testProjectionFormatter(self):
        expr = self.expr['name', self.expr.id.rename('new_id')].new_id.astype('float32')
        self._lines_eq(EXPECTED_PROJECTION_FORMAT, repr(expr))

    def testFilterFormatter(self):
        expr = self.expr[(self.expr.name != 'test') & (self.expr.id > 100)]
        self._lines_eq(EXPECTED_FILTER_FORMAT, repr(expr))

    def testSliceFormatter(self):
        expr = self.expr[:100]
        self._lines_eq(EXPECTED_SLICE_FORMAT, repr(expr))

        expr = self.expr[5:100:3]
        self._lines_eq(EXPECTED_SLICE_WITH_START_STEP_FORMAT, repr(expr))

    def testArithmeticFormatter(self):
        expr = self.expr
        d = -(expr['id']) + 20.34 - expr['id'] + float(20) * expr['id'] \
            - expr['id'] / 4.9 + 40 // 2 + expr['id'] // 1.2

        try:
            self._lines_eq(EXPECTED_ARITHMETIC_FORMAT, repr(d))
        except AssertionError as e:
            left = [to_str(line.rstrip()) for line in EXPECTED_ARITHMETIC_FORMAT.split('\n')]
            right = [to_str(line.rstrip()) for line in repr(d).split('\n')]
            self.assertEqual(len(left), len(right))
            for l, r in zip(left, right):
                try:
                    self.assertEqual(l, r)
                except AssertionError:
                    try:
                        self.assertAlmostEqual(float(l), float(r))
                    except:
                        raise e

    def testSortFormatter(self):
        expr = self.expr.sort(['name', -self.expr.id])

        self._lines_eq(EXPECTED_SORT_FORMAT, repr(expr))

    def testDistinctFormatter(self):
        expr = self.expr.distinct(['name', self.expr.id+1])

        self._lines_eq(EXPECTED_DISTINCT_FORMAT, repr(expr))

    def testGroupbyFormatter(self):
        expr = self.expr.groupby(['name', 'id']).agg(new_id=self.expr.id.sum())

        self._lines_eq(EXPECTED_GROUPBY_FORMAT, repr(expr))

        grouped = self.expr.groupby(['name'])
        expr = grouped.mutate(grouped.row_number())

        self._lines_eq(EXPECTED_MUTATE_FORMAT, repr(expr))

        expr = self.expr.groupby(['name', 'id']).count()
        self._lines_eq(EXPECTED_GROUPBY_COUNT_FORMAT, repr(expr))

    def testReductionFormatter(self):
        expr = self.expr.groupby(['id']).id.std()

        self._lines_eq(EXPECTED_REDUCTION_FORMAT, repr(expr))

        expr = self.expr.id.mean()
        self._lines_eq(EXPECTED_REDUCTION_FORMAT2, repr(expr))

        expr = self.expr.count()
        self._lines_eq(EXPECTED_REDUCTION_FORMAT3, repr(expr))

    def testWindowFormatter(self):
        expr = self.expr.groupby(['name']).sort(-self.expr.id).name.rank()

        self._lines_eq(EXPECTED_WINDOW_FORMAT1, repr(expr))

        expr = self.expr.groupby(['id']).id.cummean(preceding=10, following=5, unique=True)

        self._lines_eq(EXPECTED_WINDOW_FORMAT2, repr(expr))

    def testElementFormatter(self):
        expr = self.expr.name.contains('test')

        self._lines_eq(EXPECTED_STRING_FORMAT, repr(expr))

        expr = self.expr.id.between(1, 3)

        self._lines_eq(EXPECTED_ELEMENT_FORMAT, repr(expr))

        expr = self.expr.name.astype('datetime').strftime('%Y')

        self._lines_eq(EXPECTED_DATETIME_FORMAT, repr(expr))

        expr = self.expr.id.switch(3, self.expr.name, 4, self.expr.name + 'abc',
                                   default=self.expr.name + 'test')
        self._lines_eq(EXPECTED_SWITCH_FORMAT, repr(expr))

    def testJoinFormatter(self):
        expr = self.expr.join(self.expr2, ('name', 'name2'))
        self._lines_eq(EXPECTED_JOIN_FORMAT, repr(expr))

    def testAstypeFormatter(self):
        expr = self.expr.id.astype('float')
        self._lines_eq(EXPECTED_CAST_FORMAT, repr(expr))

if __name__ == '__main__':
    unittest.main()
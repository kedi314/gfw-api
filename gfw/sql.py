# Global Forest Watch API
# Copyright (C) 2014 World Resource Institute
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

"""This module contains SQL helpers."""


class SqlError(ValueError):
    def __init__(self, msg):
        super(SqlError, self).__init__(msg)


class FormaSqlError(SqlError):
    PARAMS = """'begin' and 'end' dates in YYYY-MM-DD format"""

    def __init__(self):
        msg = 'Invalid SQL parameters for FORMA world query: %s' % \
            self.PARAMS
        super(FormaSqlError, self).__init__(msg)


class Sql():
    pass


class FormaSql(Sql):

    # Worldwide query with optional geojson filter:
    WORLD = """
        SELECT
           count(t.*) AS value
        FROM
           forma_api t
        WHERE
            date >= '{begin}'::date
            AND date <= '{end}'::date
            {geojson}"""

    # Query by country:
    ISO = """
        SELECT
           t.iso,
           count(t.*) AS value
        FROM
           forma_api t
        WHERE
            date >= '{begin}'::date
            AND date <= '{end}'::date
            AND iso = '{iso}'
        GROUP BY
           t.iso"""

    # Query by country and administrative unit 1:
    ID1 = """
        SELECT
           g.id_1 AS id1,
           count(*) AS value
        FROM
           forma_api t
        INNER JOIN
           (
              SELECT
                 *
              FROM
                 gadm2
              WHERE
                 id_1 = {id1}
                 AND iso = '{iso}'
           ) g
              ON t.gadm2::int = g.objectid
        WHERE
           t.date >= '{begin}'::date
           AND t.date <= '{end}'
        GROUP BY
           g.id_1 id1,
        ORDER BY
           g.id_1"""

    # Query by concession use and concession polygon cartodb_id:
    USE = """
        SELECT
           p.cartodb_id AS pid,
           count(t.*) AS value
        FROM
           {use_table} u,
           forma_api f
        WHERE
           u.cartodb_id = {pid}
           AND ST_Intersects(f.the_geom, u.the_geom)
           AND f.date >= '{begin}'::date
           AND f.date <= '{end}'::date
        GROUP BY
           u.cartodb_id"""

    # Query by protected area:
    PA = """"""

    @classmethod
    def process(cls, args):
        begin = args['begin'] if 'begin' in args else '1969-01-01'
        end = args['end'] if 'end' in args else '3014-01-01'
        params = dict(begin=begin, end=end, geojson='')
        classification = cls.classify_query(args)
        if hasattr(cls, classification):
            return getattr(cls, classification)(params, args)

    @classmethod
    def world(cls, params, args):
        if 'geojson' in args:
            params['geojson'] = "AND ST_INTERSECTS(ST_SetSRID( \
                ST_GeomFromGeoJSON('%s'),4326),the_geom)" % args['geojson']
        return FormaSql.WORLD.format(**params)

    @classmethod
    def classify_query(cls, args):
        if 'iso' in args and not 'id1' in args:
            return 'iso'
        elif 'iso' in args and 'id1' in args:
            return 'id1'
        elif 'use' in args:
            return 'use'
        elif 'pa' in args:
            return 'pa'
        else:
            return 'world'

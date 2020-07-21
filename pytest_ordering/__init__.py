# -*- coding: utf-8 -*-
import operator
from warnings import warn

import pytest

from ._version import __version__

orders_map = {
    'first': 0,
    'second': 1,
    'third': 2,
    'fourth': 3,
    'fifth': 4,
    'sixth': 5,
    'seventh': 6,
    'eighth': 7,
    'last': -1,
    'second_to_last': -2,
    'third_to_last': -3,
    'fourth_to_last': -4,
    'fifth_to_last': -5,
    'sixth_to_last': -6,
    'seventh_to_last': -7,
    'eighth_to_last': -8,
}


def pytest_configure(config):
    """Register the "run" marker."""

    provided_by_pytest_ordering = (
        'Provided by pytest-ordering. '
        'See also: http://pytest-ordering.readthedocs.org/'
    )

    config_line = (
            'run: specify ordering information for when tests should run '
            'in relation to one another. ' + provided_by_pytest_ordering
    )
    config.addinivalue_line('markers', config_line)

    for mark_name in orders_map.keys():
        config_line = '{}: run test {}. {}'.format(mark_name,
                                                   mark_name.replace('_', ' '),
                                                   provided_by_pytest_ordering)
        config.addinivalue_line('markers', config_line)


def pytest_collection_modifyitems(session, config, items):
    def check_item_name(name):
        if name not in item_names:
            warn('Invalid test name {} ignoring'.format(name))
            return False
        return True

    grouped_items = {}
    dependent_items = {}
    item_names = {item.name: item for item in items}

    for item in items:
        for mark_name, order in orders_map.items():
            mark = item.get_closest_marker(mark_name)

            if mark:
                item.add_marker(pytest.mark.run(order=order))
                break

        mark = item.get_closest_marker('run')

        if mark:
            order = mark.kwargs.get('order')
            before = mark.kwargs.get('before')
            if before is not None and check_item_name(before):
                dependent_items[item.name] = before
            after = mark.kwargs.get('after')
            if after is not None and check_item_name(after):
                dependent_items[after] = item.name
        else:
            order = None

        grouped_items.setdefault(order, []).append(item)

    sorted_names = sorted_item_names(dependent_items)
    sorted_items = [item_names[name] for name in sorted_names]

    unordered_items = [[item for item in grouped_items.pop(None, [])
                        if item not in sorted_items]]
    sorted_items = [sorted_items]
    start_list = sorted((i for i in grouped_items.items() if i[0] >= 0),
                        key=operator.itemgetter(0))
    end_list = sorted((i for i in grouped_items.items() if i[0] < 0),
                      key=operator.itemgetter(0))

    sorted_items.extend([i[1] for i in start_list])
    sorted_items.extend(unordered_items)
    sorted_items.extend([i[1] for i in end_list])

    items[:] = [item for sublist in sorted_items for item in sublist]


def sorted_item_names(dependent_items):
    sorted_names = []
    for item_name, later_item_name in dependent_items.items():
        if item_name in sorted_names:
            index = sorted_names.index(item_name)
            if later_item_name in sorted_names:
                if index > sorted_names.index(later_item_name):
                    warn('Ordering {} before {} is not possible - ignoring it'
                         .format(item_name, later_item_name))
            else:
                sorted_names.insert(index + 1, later_item_name)
        elif later_item_name in sorted_names:
            index = sorted_names.index(later_item_name)
            sorted_names.insert(index, item_name)
        else:
            sorted_names.append(item_name)
            sorted_names.append(later_item_name)
    return sorted_names

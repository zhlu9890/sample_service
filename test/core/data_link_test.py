import datetime
import uuid

from pytest import raises

from core.test_utils import assert_exception_correct
from SampleService.core.data_link import DataLink
from SampleService.core.errors import MissingParameterError, IllegalParameterError
from SampleService.core.sample import SampleNodeAddress, SampleAddress
from SampleService.core.workspace import DataUnitID, UPA


def dt(timestamp):
    return datetime.datetime.fromtimestamp(timestamp, tz=datetime.timezone.utc)


def test_init_no_expire():
    sid = uuid.UUID('1234567890abcdef1234567890abcdef')

    dl = DataLink(
        uuid.UUID('1234567890abcdef1234567890abcdee'),
        DataUnitID(UPA('2/3/4')),
        SampleNodeAddress(SampleAddress(sid, 5), 'foo'),
        dt(500),
        'usera'
    )

    assert dl.id == uuid.UUID('1234567890abcdef1234567890abcdee')
    assert dl.duid == DataUnitID(UPA('2/3/4'))
    assert dl.sample_node_address == SampleNodeAddress(SampleAddress(sid, 5), 'foo')
    assert dl.created == dt(500)
    assert dl.created_by == 'usera'
    assert dl.expired is None
    assert str(dl) == ('id=12345678-90ab-cdef-1234-567890abcdee ' +
                       'duid=[2/3/4] ' +
                       'sample_node_address=[12345678-90ab-cdef-1234-567890abcdef:5:foo] ' +
                       'created=500.0 created_by=usera expired=None')


def test_init_with_expire1():
    sid = uuid.UUID('1234567890abcdef1234567890abcdef')

    dl = DataLink(
        uuid.UUID('1234567890abcdef1234567890abcdee'),
        DataUnitID(UPA('2/6/4'), 'whee'),
        SampleNodeAddress(SampleAddress(sid, 7), 'bar'),
        dt(400),
        'u',
        dt(800)
    )

    assert dl.id == uuid.UUID('1234567890abcdef1234567890abcdee')
    assert dl.duid == DataUnitID(UPA('2/6/4'), 'whee')
    assert dl.sample_node_address == SampleNodeAddress(SampleAddress(sid, 7), 'bar')
    assert dl.created == dt(400)
    assert dl.created_by == 'u'
    assert dl.expired == dt(800)
    assert str(dl) == ('id=12345678-90ab-cdef-1234-567890abcdee ' +
                       'duid=[2/6/4:whee] ' +
                       'sample_node_address=[12345678-90ab-cdef-1234-567890abcdef:7:bar] ' +
                       'created=400.0 created_by=u expired=800.0')


def test_init_with_expire2():
    sid = uuid.UUID('1234567890abcdef1234567890abcdef')

    dl = DataLink(
        uuid.UUID('1234567890abcdef1234567890abcdee'),
        DataUnitID(UPA('2/6/4'), 'whee'),
        SampleNodeAddress(SampleAddress(sid, 7), 'bar'),
        dt(400),
        'myuserᚥnameisHank',
        dt(400)
    )

    assert dl.id == uuid.UUID('1234567890abcdef1234567890abcdee')
    assert dl.duid == DataUnitID(UPA('2/6/4'), 'whee')
    assert dl.sample_node_address == SampleNodeAddress(SampleAddress(sid, 7), 'bar')
    assert dl.created == dt(400)
    assert dl.created_by == 'myuserᚥnameisHank'
    assert dl.expired == dt(400)
    assert str(dl) == ('id=12345678-90ab-cdef-1234-567890abcdee ' +
                       'duid=[2/6/4:whee] ' +
                       'sample_node_address=[12345678-90ab-cdef-1234-567890abcdef:7:bar] ' +
                       'created=400.0 created_by=myuserᚥnameisHank expired=400.0')


def test_init_fail():
    lid = uuid.UUID('1234567890abcdef1234567890abcdee')
    d = DataUnitID(UPA('1/1/1'))
    sid = uuid.UUID('1234567890abcdef1234567890abcdef')
    s = SampleNodeAddress(SampleAddress(sid, 1), 'a')
    t = dt(1)
    u = 'u'
    bt = datetime.datetime.now()

    _init_fail(None, d, s, t, u, t, ValueError('id cannot be a value that evaluates to false'))
    _init_fail(lid, None, s, t, u, t, ValueError('duid cannot be a value that evaluates to false'))
    _init_fail(lid, d, None, t, u, t, ValueError(
        'sample_node_address cannot be a value that evaluates to false'))
    _init_fail(lid, d, s, None, u, t, ValueError(
        'created cannot be a value that evaluates to false'))
    _init_fail(lid, d, s, bt, u, t, ValueError('created cannot be a naive datetime'))
    # this also kinda points to a user name class
    _init_fail(lid, d, s, t, None, t, MissingParameterError('created_by'))
    _init_fail(lid, d, s, t, '', t, MissingParameterError('created_by'))
    _init_fail(lid, d, s, t, 'foo \t bar', t, IllegalParameterError(
        'created_by contains control characters'))
    _init_fail(lid, d, s, t, u, bt, ValueError('expired cannot be a naive datetime'))
    _init_fail(lid, d, s, dt(100), u, dt(99), ValueError(
        'link cannot expire before it is created'))


def _init_fail(lid, duid, sna, cr, cru, ex, expected):
    with raises(Exception) as got:
        DataLink(lid, duid, sna, cr, cru, ex)
    assert_exception_correct(got.value, expected)


def test_equals():
    lid1 = uuid.UUID('1234567890abcdef1234567890abcdee')
    lid1a = uuid.UUID('1234567890abcdef1234567890abcdee')
    lid2 = uuid.UUID('1234567890abcdef1234567890abcdec')
    lid2a = uuid.UUID('1234567890abcdef1234567890abcdec')
    d1 = DataUnitID(UPA('1/1/1'))
    d1a = DataUnitID(UPA('1/1/1'))
    d2 = DataUnitID(UPA('1/1/2'))
    d2a = DataUnitID(UPA('1/1/2'))
    sid = uuid.UUID('1234567890abcdef1234567890abcdef')
    s1 = SampleNodeAddress(SampleAddress(sid, 1), 'foo')
    s1a = SampleNodeAddress(SampleAddress(sid, 1), 'foo')
    s2 = SampleNodeAddress(SampleAddress(sid, 2), 'foo')
    s2a = SampleNodeAddress(SampleAddress(sid, 2), 'foo')
    t1 = dt(500)
    t1a = dt(500)
    t2 = dt(600)
    t2a = dt(600)
    u1 = 'u'
    u1a = 'u'
    u2 = 'y'
    u2a = 'y'

    assert DataLink(lid1, d1, s1, t1, u1) == DataLink(lid1a, d1a, s1a, t1a, u1a)
    assert DataLink(lid1, d1, s1, t1, u1, None) == DataLink(lid1a, d1a, s1a, t1a, u1a, None)
    assert DataLink(lid2, d2, s2, t1, u2, t2) == DataLink(lid2a, d2a, s2a, t1a, u2a, t2a)

    assert DataLink(lid1, d1, s1, t1, u1) != (lid1, d1, s1, t1, u1)
    assert DataLink(lid1, d1, s1, t1, u1, t2) != (lid1, d1, s1, t1, u1, t2)

    assert DataLink(lid1, d1, s1, t1, u1) != DataLink(lid2, d1a, s1a, t1a, u1a)
    assert DataLink(lid1, d1, s1, t1, u1) != DataLink(lid1a, d2, s1a, t1a, u1a)
    assert DataLink(lid1, d1, s1, t1, u1) != DataLink(lid1a, d1a, s2, t1a, u1a)
    assert DataLink(lid1, d1, s1, t1, u1) != DataLink(lid1a, d1a, s1a, t2, u1a)
    assert DataLink(lid1, d1, s1, t1, u1) != DataLink(lid1a, d1a, s1a, t1, u2)
    assert DataLink(lid1, d1, s1, t1, u1, t2) != DataLink(lid1a, d1a, s1a, t1a, u1a, t1)
    assert DataLink(lid1, d1, s1, t1, u1, t1) != DataLink(lid1a, d1a, s1a, t1a, u1a)
    assert DataLink(lid1, d1, s1, t1, u1) != DataLink(lid1a, d1a, s1a, t1a, u1a, t1a)


def test_hash():
    # hashes will change from instance to instance of the python interpreter, and therefore
    # tests can't be written that directly test the hash value. See
    # https://docs.python.org/3/reference/datamodel.html#object.__hash__
    lid1 = uuid.UUID('1234567890abcdef1234567890abcdee')
    lid1a = uuid.UUID('1234567890abcdef1234567890abcdee')
    lid2 = uuid.UUID('1234567890abcdef1234567890abcdec')
    lid2a = uuid.UUID('1234567890abcdef1234567890abcdec')
    d1 = DataUnitID(UPA('1/1/1'))
    d1a = DataUnitID(UPA('1/1/1'))
    d2 = DataUnitID(UPA('1/1/2'))
    d2a = DataUnitID(UPA('1/1/2'))
    id_ = uuid.UUID('1234567890abcdef1234567890abcdef')
    s1 = SampleNodeAddress(SampleAddress(id_, 1), 'foo')
    s1a = SampleNodeAddress(SampleAddress(id_, 1), 'foo')
    s2 = SampleNodeAddress(SampleAddress(id_, 2), 'foo')
    s2a = SampleNodeAddress(SampleAddress(id_, 2), 'foo')
    t1 = dt(500)
    t1a = dt(500)
    t2 = dt(600)
    t2a = dt(600)
    u1 = 'u'
    u1a = 'u'
    u2 = 'y'
    u2a = 'y'

    assert hash(DataLink(lid1, d1, s1, t1, u1)) == hash(DataLink(lid1a, d1a, s1a, t1a, u1a))
    assert hash(DataLink(lid1, d1, s1, t1, u1, None)) == hash(
        DataLink(lid1a, d1a, s1a, t1a, u1a, None))
    assert hash(DataLink(lid2, d2, s2, t1, u2, t2)) == hash(
        DataLink(lid2a, d2a, s2a, t1a, u2a, t2a))

    assert hash(DataLink(lid1, d1, s1, t1, u1)) != hash(DataLink(lid2, d1a, s1a, t1a, u1a))
    assert hash(DataLink(lid1, d1, s1, t1, u1)) != hash(DataLink(lid1a, d2, s1a, t1a, u1a))
    assert hash(DataLink(lid1, d1, s1, t1, u1)) != hash(DataLink(lid1a, d1a, s2, t1a, u1a))
    assert hash(DataLink(lid1, d1, s1, t1, u1)) != hash(DataLink(lid1a, d1a, s1a, t2, u1a))
    assert hash(DataLink(lid1, d1, s1, t1, u1)) != hash(DataLink(lid1a, d1a, s1a, t1a, u2))
    assert hash(DataLink(lid1, d1, s1, t1, u1, t2)) != hash(
        DataLink(lid1a, d1a, s1a, t1a, u1a, t1))
    assert hash(DataLink(lid1, d1, s1, t1, u1, t1)) != hash(DataLink(lid1a, d1a, s1a, t1a, u1a))
    assert hash(DataLink(lid1, d1, s1, t1, u1)) != hash(DataLink(lid1a, d1a, s1a, t1a, u1a, t1a))

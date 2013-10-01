'''
Created on 19/06/2013

@author: Jose Emilio Romero Lopez
'''
import tables as tb
import time


class Event(tb.IsDescription):
    time = tb.Float64Col()
    magnitude = tb.Float64Col()
    label = tb.StringCol(16)
    description = tb.StringCol(120)


class Seismogram(object):

    def __init__(self, h5file, name, group_name='seismograms', title='',
                 fs=50.0, time=time.time(), location='', description=''):
        atom = tb.atom.Float64Atom()
        parent_group = h5file.getNode(h5file.root, group_name, 'Group')
        if name not in parent_group:
            self.group = h5file.createGroup(parent_group, name,
                                            title=title,
                                            filters=h5file.filters)
        else:
            self.group = parent_group._v_groups[name]
        if 'x' not in self.group:
            h5file.createEArray(self.group, 'x', atom, shape=(0,),
                                title='Signal')
        if 'cf' not in self.group:
            h5file.createEArray(self.group, 'cf', atom, shape=(0,),
                                title='Characteristic Function')
        if 'events' not in self.group:
            h5file.createTable(self.group, 'events', Event,
                                             title='Events')
        self.group._v_attrs.fs = fs
        self.group._v_attrs.time = time
        self.group._v_attrs.location = location
        self.group._v_attrs.description = description

    def __getattr__(self, name):
        if name == 'name':
            return self.group._v_name
        if name == 'title':
            return self.group._v_title
        if name in self.group._v_attrs:
            return self.group._v_attrs[name]
        return self.group.__getattr__(name)

    def __setattr__(self, name, value):
        if name == 'group':
            self.__dict__[name] = value
        elif name == 'title':
            self.group._v_title = value
        elif name in self.group._v_attrs:
            self.group._v_attrs[name] = value
        else:
            self.group.__setattr__(self, name, value)

    def __str__(self):
        return self.group.__str__()

    def __repr__(self):
        return self.group.__repr__()

    @staticmethod
    def is_seismogram_valid(group):
        try:
            assert 'x' in group
            assert 'cf' in group
            assert 'events' in group
            assert 'fs' in group._v_attrs
            assert 'time' in group._v_attrs
            assert 'location' in group._v_attrs
            assert 'description' in group._v_attrs
        except AssertionError:
            print 'No'
            return False
        return True


class Document(tb.File):

    def __init__(self, filename, title='Seismograms', group_name='seismograms',
                 complevel=0, complib='blosc'):
        super(Document, self).__init__(filename, mode='a', title=title,
                                       filters=tb.Filters(complevel=complevel,
                                                         complib=complib))
        if not '/' + group_name in self:
            self.createGroup(self.root, group_name, title)

    def create_seismogram(self, name, fs, group_name='seismograms', **kwargs):
        seismogram = Seismogram(self, name, group_name=group_name, **kwargs)
        self.flush()
        return seismogram

    def delete_seismogram(self, name, group_name='seismograms'):
        group = self.getNode(self.root, group_name, 'Group')
        if Seismogram.is_seismogram_valid(group):
            self.removeNode('/' + group_name, name, recursive=True)

    def seismograms(self, group_name='seismograms'):
        parent_group = self.getNode(self.root, group_name)
        for g in parent_group._v_groups:
            group = parent_group._v_groups[g]
            if Seismogram.is_seismogram_valid(group):
                yield Seismogram(self, g, group_name=group_name)

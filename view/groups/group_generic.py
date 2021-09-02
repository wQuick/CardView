#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2021      Christopher Horn
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
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#

"""
GenericGrampsFrameGroup
"""

# ------------------------------------------------------------------------
#
# GTK modules
#
# ------------------------------------------------------------------------
from gi.repository import Gtk

from ..frames.frame_citation import CitationGrampsFrame

# ------------------------------------------------------------------------
#
# Plugin modules
#
# ------------------------------------------------------------------------
from ..frames.frame_classes import GrampsOptions
from ..frames.frame_couple import CoupleGrampsFrame
from ..frames.frame_event import EventGrampsFrame
from ..frames.frame_image import ImageGrampsFrame
from ..frames.frame_note import NoteGrampsFrame
from ..frames.frame_person import PersonGrampsFrame
from ..frames.frame_place import PlaceGrampsFrame
from ..frames.frame_repository import RepositoryGrampsFrame
from ..frames.frame_source import SourceGrampsFrame
from .group_list import GrampsFrameGroupList


# ------------------------------------------------------------------------
#
# GenericGrampsFrameGroup class
#
# ------------------------------------------------------------------------
class GenericGrampsFrameGroup(GrampsFrameGroupList):
    """
    The GenericGrampsFrameGroup class provides a container for managing a
    set of generic frames for a list of primary Gramps objects.
    """

    def __init__(self, grstate, groptions, frame_obj_type, frame_obj_handles):
        GrampsFrameGroupList.__init__(
            self, grstate, groptions, enable_drop=False
        )
        self.obj_type = frame_obj_type
        self.obj_handles = frame_obj_handles

        if frame_obj_type == "Tuples":
            tuple_list = frame_obj_handles
        else:
            tuple_list = [(frame_obj_type, x) for x in frame_obj_handles]

        groups = {
            "data": Gtk.SizeGroup(mode=Gtk.SizeGroupMode.HORIZONTAL),
            "metadata": Gtk.SizeGroup(mode=Gtk.SizeGroupMode.HORIZONTAL),
            "image": Gtk.SizeGroup(mode=Gtk.SizeGroupMode.HORIZONTAL),
        }

        for obj_type, obj_handle in tuple_list:
            if obj_type not in [
                "Person",
                "Family",
                "Event",
                "Place",
                "Media",
                "Note",
                "Source",
                "Citation",
                "Repository",
            ]:
                continue
            groptions = GrampsOptions(
                "options.group.{}".format(obj_type.lower()), size_groups=groups
            )
            obj = self.fetch(obj_type, obj_handle)
            if obj_type == "Person":
                frame = PersonGrampsFrame(grstate, groptions, obj)
            elif obj_type == "Family":
                frame = CoupleGrampsFrame(grstate, groptions, obj)
            elif obj_type == "Event":
                frame = EventGrampsFrame(
                    grstate,
                    groptions,
                    None,
                    obj,
                    None,
                    None,
                    None,
                    None,
                )
            elif obj_type == "Place":
                frame = PlaceGrampsFrame(grstate, groptions, obj)
            elif obj_type == "Media":
                frame = ImageGrampsFrame(grstate, groptions, obj)
            elif obj_type == "Note":
                frame = NoteGrampsFrame(grstate, groptions, obj)
            elif obj_type == "Source":
                frame = SourceGrampsFrame(grstate, groptions, obj)
            elif obj_type == "Citation":
                frame = CitationGrampsFrame(grstate, groptions, obj)
            elif obj_type == "Repository":
                frame = RepositoryGrampsFrame(grstate, groptions, obj)
            else:
                continue
            self.add_frame(frame)
        self.show_all()

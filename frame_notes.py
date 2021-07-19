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
NotesGrampsFrameGroup
"""

# ------------------------------------------------------------------------
#
# GTK modules
#
# ------------------------------------------------------------------------
from gi.repository import Gtk


# ------------------------------------------------------------------------
#
# Gramps modules
#
# ------------------------------------------------------------------------
from gramps.gen.const import GRAMPS_LOCALE as glocale
from gramps.gen.db import DbTxn


# ------------------------------------------------------------------------
#
# Plugin modules
#
# ------------------------------------------------------------------------
from frame_list import GrampsFrameList
from frame_note import NoteGrampsFrame
from frame_utils import get_gramps_object_type


# ------------------------------------------------------------------------
#
# NotesGrampsFrameGroup class
#
# ------------------------------------------------------------------------
class NotesGrampsFrameGroup(GrampsFrameList):
    """
    The NotesGrampsFrameGroup class provides a container for managing all
    of the notes associated with an object.
    """

    def __init__(self, grstate, obj):
        GrampsFrameList.__init__(self, grstate)
        self.obj = obj
        self.obj_type, discard1, discard2 = get_gramps_object_type(obj)

        groups = {
            "data": Gtk.SizeGroup(mode=Gtk.SizeGroupMode.HORIZONTAL),
            "metadata": Gtk.SizeGroup(mode=Gtk.SizeGroupMode.HORIZONTAL),
        }

        for handle in obj.get_note_list():
            note = grstate.dbstate.db.get_note_from_handle(handle)
            frame = NoteGrampsFrame(
                grstate,
                "note",
                note,
                groups=groups,
            )
            self.add_frame(frame)
        self.show_all()

    # Todo: Add drag and drop to reorder or add to note list
    def save_new_object(self, handle, insert_row):
        """
        Add new note to the list.
        """
        return

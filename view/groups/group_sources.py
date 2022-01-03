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
SourcesFrameGroup
"""

# ------------------------------------------------------------------------
#
# Gramps modules
#
# ------------------------------------------------------------------------
from gramps.gen.const import GRAMPS_LOCALE as glocale

# ------------------------------------------------------------------------
#
# Plugin modules
#
# ------------------------------------------------------------------------
from ..frames import SourceFrame
from .group_list import FrameGroupList

_ = glocale.translation.sgettext


# ------------------------------------------------------------------------
#
# SourcesFrameGroup class
#
# ------------------------------------------------------------------------
class SourcesFrameGroup(FrameGroupList):
    """
    The SourcesFrameGroup class provides a container for viewing and
    managing all of the sources associated with a primary Gramps object.
    """

    def __init__(self, grstate, groptions, obj):
        FrameGroupList.__init__(
            self, grstate, groptions, obj, enable_drop=False
        )
        sources_list = []
        if self.group_base.obj_type == "Repository":
            for (
                obj_type,
                obj_handle,
            ) in grstate.dbstate.db.find_backlink_handles(
                self.group_base.obj.get_handle()
            ):
                if obj_type == "Source":
                    source = self.fetch("Source", obj_handle)
                    sources_list.append(source)

        maximum = grstate.config.get("options.global.max.sources-per-group")
        sources_list = sources_list[:maximum]

        if sources_list:
            for source in sources_list:
                frame = SourceFrame(
                    grstate,
                    groptions,
                    source,
                )
                self.add_frame(frame)
        self.show_all()

    # Todo
    def save_new_object(self, handle, insert_row):
        """
        Add new source to the repository.
        """

# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2001-2007  Donald N. Allingham
# Copyright (C) 2009-2010  Gary Burton
# Copyright (C) 2015-2016  Nick Hall
# Copyright (C) 2021       Christopher Horn
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
Combined Profile View
"""

# -------------------------------------------------------------------------
#
# Python modules
#
# -------------------------------------------------------------------------
import pickle


# -------------------------------------------------------------------------
#
# GTK/Gnome modules
#
# -------------------------------------------------------------------------
from gi.repository import Gtk


# -------------------------------------------------------------------------
#
# Gramps Modules
#
# -------------------------------------------------------------------------
from gramps.gen.config import config as global_config
from gramps.gen.const import CUSTOM_FILTERS
from gramps.gen.const import GRAMPS_LOCALE as glocale
from gramps.gen.errors import WindowActiveError
from gramps.gen.utils.db import navigation_label
from gramps.gui.editors import FilterEditor
from gramps.gui.views.bookmarks import PersonBookmarks

from enavigationview import ENavigationView
from view.frames.frame_utils import get_config_option, save_config_option
from view.pages.page_options import CONFIGSETTINGS
from view.pages.page_person import PersonProfilePage
from view.pages.page_family import FamilyProfilePage
from view.pages.page_event import EventProfilePage
from view.pages.page_media import MediaProfilePage
from view.pages.page_name import NameProfilePage
from view.pages.page_note import NoteProfilePage
from view.pages.page_place import PlaceProfilePage
from view.pages.page_citation import CitationProfilePage
from view.pages.page_child_ref import ChildRefProfilePage
from view.pages.page_source import SourceProfilePage
from view.pages.page_repository import RepositoryProfilePage
from view.pages.page_person_ref import PersonRefProfilePage

_ = glocale.translation.sgettext


class ProfileView(ENavigationView):
    """
    View showing a textual representation of the relationships and events of
    the active person.
    """

    # Kept separate due to sheer number of them
    CONFIGSETTINGS = CONFIGSETTINGS

    def __init__(self, pdata, dbstate, uistate, nav_group=0):
        ENavigationView.__init__(
            self,
            _("Profile"),
            pdata,
            dbstate,
            uistate,
            PersonBookmarks,
            nav_group,
        )
        self.header = None
        self.vbox = None
        self.child = None
        self.scroll = None
        self.viewport = None
        self.dirty = False
        self.redrawing = False
        self.active_type = None

        self.loaded = False
        self.passed_uistate = uistate
        self.passed_navtype = None
        if uistate.viewmanager.active_page:
            self.passed_navtype = (
                uistate.viewmanager.active_page.navigation_type()
            )

        dbstate.connect("database-changed", self.change_db)
        uistate.connect("nameformat-changed", self.build_tree)
        uistate.connect("placeformat-changed", self.build_tree)

        self.pages = {}
        self._add_page(
            PersonProfilePage(self.dbstate, self.uistate, self._config)
        )
        self._add_page(
            NameProfilePage(self.dbstate, self.uistate, self._config)
        )
        self._add_page(
            ChildRefProfilePage(self.dbstate, self.uistate, self._config)
        )
        self._add_page(
            PersonRefProfilePage(self.dbstate, self.uistate, self._config)
        )
        self._add_page(
            FamilyProfilePage(self.dbstate, self.uistate, self._config)
        )
        self._add_page(
            EventProfilePage(self.dbstate, self.uistate, self._config)
        )
        self._add_page(
            CitationProfilePage(self.dbstate, self.uistate, self._config)
        )
        self._add_page(
            SourceProfilePage(self.dbstate, self.uistate, self._config)
        )
        self._add_page(
            RepositoryProfilePage(self.dbstate, self.uistate, self._config)
        )
        self._add_page(
            MediaProfilePage(self.dbstate, self.uistate, self._config)
        )
        self._add_page(
            NoteProfilePage(self.dbstate, self.uistate, self._config)
        )
        self._add_page(
            PlaceProfilePage(self.dbstate, self.uistate, self._config)
        )
        self.active_page = None
        self.additional_uis.append(self.additional_ui)

    def _add_page(self, page):
        page.connect("object-changed", self.object_changed)
        page.connect("context-changed", self.context_changed)
        page.connect("copy-to-clipboard", self.clipboard_copy)
        self.pages[page.page_type()] = page

    def _connect_db_signals(self):
        """
        Register the callbacks we need.
        """
        for obj in [
            "person",
            "family",
            "event",
            "place",
            "source",
            "citation",
            "media",
            "repository",
            "note",
        ]:
            self.callman.add_db_signal("{}-add".format(obj), self.redraw)
            self.callman.add_db_signal("{}-update".format(obj), self.redraw)
            self.callman.add_db_signal("{}-delete".format(obj), self.redraw)
            self.callman.add_db_signal("{}-rebuild".format(obj), self.redraw)

    def navigation_type(self):
        return self.active_type

    def can_configure(self):
        """
        See :class:`~gui.views.pageview.PageView
        :return: bool
        """
        return True

    def config_connect(self):
        """
        Monitor configuration options for changes.
        """
        for item in self.CONFIGSETTINGS:
            self._config.connect(item[0], self.config_update)

    def config_update(self, client, cnxn_id, entry, data):
        #        for page in self.pages.values():
        #            page.config_update()
        self.redraw()

    def _get_configure_page_funcs(self):
        """
        Return functions to build configuration dialog for a page.
        """
        return self.active_page._get_configure_page_funcs()

    def goto_handle(self, handle):
        self.change_object(handle)

    def build_tree(self):
        self.redraw()

    def change_page(self):
        if not self.history.history:
            if self.passed_uistate and self.passed_navtype:
                self.loaded = self.seed_history()
            if not self.loaded:
                obj_tuple = self._get_last()
                if obj_tuple:
                    self.history.push(tuple(obj_tuple))
                    self.loaded = True
        ENavigationView.change_page(self)
        self.uistate.clear_filter_results()

    def seed_history(self):
        """
        A hack that attempts to seed our history cache with last object
        using the uistate copy as the views may be using divergent history
        navigation classes.
        """
        if not self.passed_uistate.history_lookup:
            return False
        for navobj in self.passed_uistate.history_lookup:
            objtype, navtype = navobj
            if objtype == self.passed_navtype:
                objhist = self.passed_uistate.history_lookup[navobj]
                if objhist and objhist.present():
                    handle = objhist.present()
                    lastobj = (objtype, handle)
                    self.history.push(lastobj)
                    return True
        return False

    def get_stock(self):
        """
        Return the name of the stock icon to use for the display.
        This assumes that this icon has already been registered with
        GNOME as a stock icon.
        """
        return "gramps-relation"

    def get_viewtype_stock(self):
        """Type of view in category"""
        return "gramps-relation"

    def build_widget(self):
        """
        Build the widget that contains the view, see
        :class:`~gui.views.pageview.PageView
        """
        container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        container.set_border_width(6)
        self.header = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.child = None
        self.scroll = Gtk.ScrolledWindow(hexpand=True, vexpand=True)
        self.scroll.set_policy(
            Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC
        )
        self.viewport = Gtk.Viewport()
        self.viewport.add(self.vbox)
        self.scroll.add(self.viewport)
        container.pack_start(self.header, False, False, 0)
        container.pack_end(self.scroll, True, True, 0)
        container.show_all()
        return container

    additional_ui = [  # Defines the UI string for UIManager
        """
      <placeholder id="CommonGo">
      <section>
        <item>
          <attribute name="action">win.Back</attribute>
          <attribute name="label" translatable="yes">_Add Bookmark</attribute>
        </item>
        <item>
          <attribute name="action">win.Forward</attribute>
          <attribute name="label" translatable="yes">"""
        """Organize Bookmarks...</attribute>
        </item>
      </section>
      <section>
        <item>
          <attribute name="action">win.HomePerson</attribute>
          <attribute name="label" translatable="yes">_Home</attribute>
        </item>
      </section>
      </placeholder>
""",
        """
      <placeholder id='otheredit'>
        <item>
          <attribute name="action">win.Edit</attribute>
          <attribute name="label" translatable="yes">Edit...</attribute>
        </item>
        <item>
          <attribute name="action">win.AddParents</attribute>
          <attribute name="label" translatable="yes">"""
        """Add New Parents...</attribute>
        </item>
        <item>
          <attribute name="action">win.ShareFamily</attribute>
          <attribute name="label" translatable="yes">"""
        """Add Existing Parents...</attribute>
        </item>
        <item>
          <attribute name="action">win.AddSpouse</attribute>
          <attribute name="label" translatable="yes">Add Partner...</attribute>
        </item>
        <item>
          <attribute name="action">win.ChangeOrder</attribute>
          <attribute name="label" translatable="yes">_Reorder</attribute>
        </item>
        <item>
          <attribute name="action">win.AddParticipant</attribute>
          <attribute name="label" translatable="yes">Add Participant...</attribute>
        </item>
        <item>
          <attribute name="action">win.FilterEdit</attribute>
          <attribute name="label" translatable="yes">"""
        """Person Filter Editor</attribute>
        </item>
      </placeholder>
""",
        """
      <section id="AddEditBook">
        <item>
          <attribute name="action">win.AddBook</attribute>
          <attribute name="label" translatable="yes">_Add Bookmark</attribute>
        </item>
        <item>
          <attribute name="action">win.EditBook</attribute>
          <attribute name="label" translatable="no">%s...</attribute>
        </item>
      </section>
"""
        % _("Organize Bookmarks"),  # Following are the Toolbar items
        """
    <placeholder id='CommonNavigation'>
    <child groups='RO'>
      <object class="GtkToolButton">
        <property name="icon-name">go-previous</property>
        <property name="action-name">win.Back</property>
        <property name="tooltip_text" translatable="yes">"""
        """Go to the previous object in the history</property>
        <property name="label" translatable="yes">_Back</property>
        <property name="use-underline">True</property>
      </object>
      <packing>
        <property name="homogeneous">False</property>
      </packing>
    </child>
    <child groups='RO'>
      <object class="GtkToolButton">
        <property name="icon-name">go-next</property>
        <property name="action-name">win.Forward</property>
        <property name="tooltip_text" translatable="yes">"""
        """Go to the next object in the history</property>
        <property name="label" translatable="yes">_Forward</property>
        <property name="use-underline">True</property>
      </object>
      <packing>
        <property name="homogeneous">False</property>
      </packing>
    </child>
    <child groups='RO'>
      <object class="GtkToolButton">
        <property name="icon-name">go-home</property>
        <property name="action-name">win.HomePerson</property>
        <property name="tooltip_text" translatable="yes">"""
        """Go to the default person</property>
        <property name="label" translatable="yes">_Home</property>
        <property name="use-underline">True</property>
      </object>
      <packing>
        <property name="homogeneous">False</property>
      </packing>
    </child>
    </placeholder>
""",
        """
    <placeholder id='BarCommonEdit'>
    <child groups='RO'>
      <object class="GtkToolButton" id="EditButton">
        <property name="icon-name">gtk-edit</property>
        <property name="action-name">win.Edit</property>
        <property name="tooltip_text" translatable="yes">"""
        """Edit the active person</property>
        <property name="label" translatable="yes">Edit...</property>
      </object>
      <packing>
        <property name="homogeneous">False</property>
      </packing>
    </child>
    <child groups='Family'>
      <object class="GtkToolButton">
        <property name="icon-name">gramps-parents-add</property>
        <property name="action-name">win.AddParents</property>
        <property name="tooltip_text" translatable="yes">"""
        """Add a new set of parents</property>
        <property name="label" translatable="yes">Add</property>
      </object>
      <packing>
        <property name="homogeneous">False</property>
      </packing>
    </child>
    <child groups='Family'>
      <object class="GtkToolButton">
        <property name="icon-name">gramps-parents-open</property>
        <property name="action-name">win.ShareFamily</property>
        <property name="tooltip_text" translatable="yes">"""
        """Add person as child to an existing family</property>
        <property name="label" translatable="yes">Share</property>
      </object>
      <packing>
        <property name="homogeneous">False</property>
      </packing>
    </child>
    <child groups='Family'>
      <object class="GtkToolButton">
        <property name="icon-name">gramps-spouse</property>
        <property name="action-name">win.AddSpouse</property>
        <property name="tooltip_text" translatable="yes">"""
        """Add a new family with person as parent</property>
        <property name="label" translatable="yes">Partner</property>
      </object>
      <packing>
        <property name="homogeneous">False</property>
      </packing>
    </child>
    <child groups='ChangeOrder'>
      <object class="GtkToolButton">
        <property name="icon-name">view-sort-ascending</property>
        <property name="action-name">win.ChangeOrder</property>
        <property name="tooltip_text" translatable="yes">"""
        """Change order of parents and families</property>
        <property name="label" translatable="yes">_Reorder</property>
        <property name="use-underline">True</property>
      </object>
      <packing>
        <property name="homogeneous">False</property>
      </packing>
    </child>
    <child groups='Event'>
      <object class="GtkToolButton">
        <property name="icon-name">gramps-parents-add</property>
        <property name="action-name">win.AddParticipant</property>
        <property name="tooltip_text" translatable="yes">"""
        """Add a new participant to the event</property>
        <property name="label" translatable="yes">_Reorder</property>
        <property name="use-underline">True</property>
      </object>
      <packing>
        <property name="homogeneous">False</property>
      </packing>
    </child>
    <child groups='Event'>
      <object class="GtkToolButton">
        <property name="icon-name">gramps-parents-open</property>
        <property name="action-name">win.ShareParticipant</property>
        <property name="tooltip_text" translatable="yes">"""
        """Add an existing participant to the event</property>
        <property name="label" translatable="yes">_Reorder</property>
        <property name="use-underline">True</property>
      </object>
      <packing>
        <property name="homogeneous">False</property>
      </packing>
    </child>
    </placeholder>
     """,
    ]

    def define_actions(self):
        ENavigationView.define_actions(self)
        for page in self.pages.values():
            page.define_actions(self)

        self._add_action("Edit", self.edit_active, "<PRIMARY>Return")
        self._add_action("FilterEdit", callback=self.filter_editor)
        self._add_action("PRIMARY-J", self.jump, "<PRIMARY>J")

    def filter_editor(self, *obj):
        try:
            FilterEditor("Person", CUSTOM_FILTERS, self.dbstate, self.uistate)
        except WindowActiveError:
            return

    def edit_active(self, *obj):
        self.active_page.edit_active()

    def change_db(self, db):
        self._change_db(db)
        if self.active:
            self.bookmarks.redraw()
        self.history.clear()
        self.redraw(None)

    def redraw(self, *obj):
        if self.active:
            active_object = self.get_active()
            if active_object:
                self.change_object(active_object)
            else:
                self.change_object(None)
        else:
            self.dirty = True

    def _get_last(self):
        dbid = self.dbstate.db.get_dbid()
        if not dbid:
            return None
        try:
            obj_tuple = get_config_option(
                self._config, "options.active.last_object", dbid=dbid
            )
        except ValueError:
            return None
        if not obj_tuple or len(obj_tuple) != 2:
            initial_person = self.dbstate.db.find_initial_person()
            if not initial_person:
                return None
            obj_tuple = ("Person", initial_person.get_handle())
        return obj_tuple

    def clipboard_copy(self, data, handle):
        return self.copy_to_clipboard(data, [handle])

    def object_changed(self, obj_type, handle):
        self.change_active((obj_type, handle))
        self.change_object((obj_type, handle))

    def _clear_change(self):
        list(map(self.header.remove, self.header.get_children()))
        list(map(self.vbox.remove, self.vbox.get_children()))
        if not self.dbstate.is_open():
            self.uistate.status.pop(self.uistate.status_id)
            self.uistate.status.push(
                self.uistate.status_id, _("No active object")
            )
        return False

    def context_changed(self, obj_type, data):
        """
        Change the page view without changing the active object.
        """
        if not obj_type or not data:
            return
        try:
            primary, secondary_type, secondary = pickle.loads(data)
        except pickle.UnpicklingError:
            return
        self.render_page(
            secondary_type,
            primary_obj=primary,
            primary_obj_type=obj_type,
            secondary_obj=secondary,
            secondary_obj_type=secondary_type,
        )
        return True

    def change_object(self, obj_tuple):
        """
        Change the page view to load a new active object.
        """
        if self.redrawing:
            return False

        if not obj_tuple:
            obj_tuple = self._get_last()
            if not obj_tuple:
                return self._clear_change()
            self.history.push(tuple(obj_tuple))
            self.loaded = True
            return False

        (
            obj_type,
            handle,
        ) = obj_tuple
        query_method = self.dbstate.db.method("get_%s_from_handle", obj_type)
        obj = query_method(handle)
        self.render_page(obj_type, primary_obj=obj, primary_obj_type=obj_type)

        if self.loaded:
            dbid = self.dbstate.db.get_dbid()
            save_config_option(
                self._config,
                "options.active.last_object",
                obj_type,
                handle,
                dbid=dbid,
            )
        return True

    def render_page(
        self,
        page_type,
        primary_obj=None,
        primary_obj_type=None,
        secondary_obj=None,
        secondary_obj_type=None,
    ):
        """
        Render a new page view.
        """
        self.redrawing = True
        if self.active_page:
            self.active_page.disable_actions(self.uimanager)

        list(map(self.header.remove, self.header.get_children()))
        list(map(self.header.remove, self.vbox.get_children()))

        page = self.pages[page_type]
        page.render_page(
            self.header, self.vbox, primary_obj, secondary=secondary_obj
        )
        page.enable_actions(self.uimanager, primary_obj)
        self.uimanager.update_menu()

        edit_button = self.uimanager.get_widget("EditButton")
        if edit_button:
            tooltip = ""
            if primary_obj_type == "Person":
                tooltip = _("Edit the active person")
            elif primary_obj_type == "Family":
                tooltip = _("Edit the active family")
            elif primary_obj_type == "Event":
                tooltip = _("Edit the active event")
            elif primary_obj_type == "Note":
                tooltip = _("Edit the active note")
            elif primary_obj_type == "Media":
                tooltip = _("Edit the active media")
            elif primary_obj_type == "Place":
                tooltip = _("Edit the active place")
            elif primary_obj_type == "Citation":
                tooltip = _("Edit the active citation")
            elif primary_obj_type == "Source":
                tooltip = _("Edit the active source")
            elif primary_obj_type == "Repository":
                tooltip = _("Edit the active repository")
            if tooltip:
                edit_button.set_tooltip_text(tooltip)

        self.uistate.modify_statusbar(self.dbstate)
        self.redrawing = False
        self.dirty = False

        self.active_page = page
        self.active_type = primary_obj_type
        name, _obj = navigation_label(
            self.dbstate.db, primary_obj_type, primary_obj.get_handle()
        )
        if (
            primary_obj_type == "Person"
            and global_config.get("interface.statusbar") > 1
        ):
            relation = self.uistate.display_relationship(
                self.dbstate, primary_obj.get_handle()
            )
            if relation:
                name = "{} ({})".format(name, relation.strip())
        if name:
            self.uistate.status.pop(self.uistate.status_id)
            self.uistate.status.push(self.uistate.status_id, name)

    def set_active(self):
        """
        Called when the page is displayed.
        """
        ENavigationView.set_active(self)
        self.uistate.viewmanager.tags.tag_enable(update_menu=False)

    def set_inactive(self):
        """
        Called when the page is no longer displayed.
        """
        ENavigationView.set_inactive(self)
        self.uistate.viewmanager.tags.tag_disable()

    def selected_handles(self):
        return [self.get_active()]

    def add_tag(self, trans, object_handle, tag_handle):
        """
        Add the given tag to the active object.
        """
        self.active_page.add_tag(trans, object_handle, tag_handle)

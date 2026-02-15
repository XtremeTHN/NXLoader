import math
import enum
from gi.repository import Adw, Gtk, GObject, Graphene, Gdk

class Color(enum.IntEnum):
    WHIITE=0
    ERROR=1
    WARNING=2
    SUCCESS=3

class CircularProgressPaintable(GObject.Object, Gdk.Paintable, Gtk.SymbolicPaintable):
    __gtype_name__ = "CircularProgressPaintable"
    widget: Gtk.Widget = GObject.Property(type=Gtk.Widget)

    __gsignals__ = {
        "animation-done": (GObject.SIGNAL_RUN_FIRST, None, tuple())
    }

    def __init__(self, widget: Gtk.Widget, done_icon_name: str):
        super().__init__()

        self.__icon_name = None
        self.__progress = 0.0

        self.widget = widget
        self.color = Color.WHIITE

        self.check_paintable: Gtk.IconPaintable = None
        self.check_progress: float = 0.0
        self.done_animation: Adw.TimedAnimation = None

        widget.connect("notify::scale-factor", self.on_scale_change)

        self.icon_name = done_icon_name
        self.hide = False
    
    def set_color(self, color: Color):
        self.color = color
        self.invalidate_contents()

    def do_snapshot_symbolic(self, snapshot: Gtk.Snapshot, width, height, colors, _):
        if self.check_progress < 1:
            snapshot.save()
            snapshot.translate(Graphene.Point().init(width / 2.0, height / 2.0))
            snapshot.scale(1.0 - self.check_progress, 1.0 - self.check_progress)
            snapshot.translate(Graphene.Point().init(-width / 2.0, -height / 2.0))
            snapshot.restore()

        if self.check_progress > 0:
            snapshot.save()
            snapshot.translate(Graphene.Point().init(width / 2.0, height / 2.0))
            snapshot.scale(self.check_progress, self.check_progress)
            snapshot.translate(Graphene.Point().init(-width / 2.0, -height / 2.0))
            Gtk.SymbolicPaintable.snapshot_symbolic(
                self.check_paintable, snapshot, width, height, colors
            )
            snapshot.restore()

        ctx = snapshot.append_cairo(Graphene.Rect().init(-2, -2, width + 4, width + 4))
        arc_end = self.progress * math.pi * 2 - math.pi / 2

        ctx.translate(width / 2.0, height / 2.0)
        
        color = colors[self.color]
        if self.check_progress > 0:
            color.alpha = color.alpha - self.check_progress
        ctx.set_source_rgba(color.red, color.green, color.blue, color.alpha)

        ctx.arc(0, 0, width / 2.0 + 1, -math.pi / 2, arc_end)
        ctx.stroke()

        rgba = color.copy()
        if self.check_progress > 0:
            rgba.alpha = (rgba.alpha * 0.25) - self.check_progress
        else:
            rgba.alpha *= 0.25

        ctx.set_source_rgba(rgba.red, rgba.green, rgba.blue, rgba.alpha)
        ctx.arc(0, 0, width / 2.0 + 1, arc_end, 3.0 * math.pi / 2.0)
        ctx.stroke()

    def __on_anim_done(self, val):
        self.check_progress = val
        self.invalidate_contents()

    def __on_anim_done_done(self, *_):
        if self.check_progress > 0.5:
            self.done_animation.set_value_from(1)
            self.done_animation.set_value_to(0)
        else:
            self.done_animation = None
            self.emit("animation-done")

    def animate_done(self):
        if self.done_animation:
            return

        self.hide = True
        target = Adw.CallbackAnimationTarget.new(self.__on_anim_done)
        self.done_animation = Adw.TimedAnimation.new(self.widget, 0, 1, 500, target)
        self.done_animation.connect("done", self.__on_anim_done_done)

        self.done_animation.set_easing(Adw.Easing.EASE_IN_OUT_CUBIC)
        self.done_animation.play()

    @GObject.Property(type=str)
    def icon_name(self):
        return self.__icon_name

    @icon_name.setter
    def icon_name(self, value):
        self.__icon_name = value
        self.cache_icons()

    @GObject.Property(type=float)
    def progress(self):
        return self.__progress

    @progress.setter
    def progress(self, value):
        if value >= 1:
            value = 1
        if value < 0:
            value = 0
        
        self.__progress = value
        self.invalidate_contents()

    def get_intrinsic_height(self):
        return 16 * self.widget.get_scale_factor()

    def get_intrinsic_width(self):
        return 16 * self.widget.get_scale_factor()

    def on_scale_change(self, *_):
        self.cache_icons()
        self.invalidate_size()
    
    def set_fraction(self, fraction):
        self.progress = fraction

    def cache_icons(self):
        if not self.icon_name:
            return

        display = self.widget.get_display()
        theme = Gtk.IconTheme.get_for_display(display)
        scale = self.widget.get_scale_factor()
        direction = self.widget.get_direction()

        self.check_paintable = theme.lookup_icon(
            self.icon_name,
            None,
            16,
            scale,
            direction,
            Gtk.IconLookupFlags.FORCE_SYMBOLIC,
        )

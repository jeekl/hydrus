import ClientCaches
import ClientConstants as CC
import HydrusConstants as HC
import HydrusData
import HydrusGlobals
import os
import wx

CHILD_POSITION_PADDING = 50
FUZZY_PADDING = 30

def GetSafePosition( position ):
    
    ( p_x, p_y ) = position
    
    # some window managers size the windows just off screen to cut off borders
    # so choose a test position that's a little more lenient
    ( test_x, test_y ) = ( p_x + FUZZY_PADDING, p_y + FUZZY_PADDING )
    
    display_index = wx.Display.GetFromPoint( ( test_x, test_y ) )
    
    if display_index == wx.NOT_FOUND:
        
        return wx.DefaultPosition
        
    else:
        
        return position
        
    
def GetSafeSize( tlw, min_size, gravity ):
    
    ( min_width, min_height ) = min_size
    
    parent = tlw.GetParent()
    
    if parent is None:
        
        width = min_width
        height = min_height
        
    else:
        
        ( parent_window_width, parent_window_height ) = parent.GetTopLevelParent().GetSize()
        
        max_width = parent_window_width - 2 * CHILD_POSITION_PADDING
        max_height = parent_window_height - 2 * CHILD_POSITION_PADDING
        
        ( width_gravity, height_gravity ) = gravity
        
        if width_gravity == -1:
            
            width = min_width
            
        else:
            
            width = int( width_gravity * max_width )
            
        
        if height_gravity == -1:
            
            height = min_height
            
        else:
            
            height = int( height_gravity * max_height )
            
        
    
    ( display_width, display_height ) = wx.GetDisplaySize()
    
    width = min( display_width, width )
    height = min( display_height, height )
    
    return ( width, height )
    
def ExpandTLWIfPossible( tlw, frame_key, desired_size_delta ):
    
    new_options = HydrusGlobals.client_controller.GetNewOptions()
    
    ( remember_size, remember_position, last_size, last_position, default_gravity, default_position, maximised, fullscreen ) = new_options.GetFrameLocation( frame_key )
    
    if not tlw.IsMaximized() and not tlw.IsFullScreen():
        
        ( current_width, current_height ) = tlw.GetSize()
        
        ( desired_delta_width, desired_delta_height ) = desired_size_delta
        
        min_width = current_width + desired_delta_width + FUZZY_PADDING
        min_height = current_height + desired_delta_height + FUZZY_PADDING
        
        ( width, height ) = GetSafeSize( tlw, ( min_width, min_height ), default_gravity )
        
        if width > current_width or height > current_height:
            
            tlw.SetSize( ( width, height ) )
            
        
    
def SaveTLWSizeAndPosition( tlw, frame_key ):
    
    new_options = HydrusGlobals.client_controller.GetNewOptions()
    
    ( remember_size, remember_position, last_size, last_position, default_gravity, default_position, maximised, fullscreen ) = new_options.GetFrameLocation( frame_key )
    
    maximised = tlw.IsMaximized()
    fullscreen = tlw.IsFullScreen()
    
    if not ( maximised or fullscreen ):
        
        safe_position = GetSafePosition( tlw.GetPositionTuple() )
        
        if safe_position != wx.DefaultPosition:
            
            last_size = tlw.GetSizeTuple()
            last_position = safe_position
            
        
    
    new_options.SetFrameLocation( frame_key, remember_size, remember_position, last_size, last_position, default_gravity, default_position, maximised, fullscreen )
    
def SetTLWSizeAndPosition( tlw, frame_key ):
    
    new_options = HydrusGlobals.client_controller.GetNewOptions()
    
    ( remember_size, remember_position, last_size, last_position, default_gravity, default_position, maximised, fullscreen ) = new_options.GetFrameLocation( frame_key )
    
    parent = tlw.GetParent()
    
    if remember_size and last_size is not None:
        
        ( width, height ) = last_size
        
    else:
        
        ( min_width, min_height ) = tlw.GetEffectiveMinSize()
        
        min_width += FUZZY_PADDING
        min_height += FUZZY_PADDING
        
        ( width, height ) = GetSafeSize( tlw, ( min_width, min_height ), default_gravity )
        
    
    tlw.SetInitialSize( ( width, height ) )
    
    min_width = min( 240, width )
    min_height = min( 240, height )
    
    tlw.SetMinSize( ( min_width, min_height ) )
    
    #
    
    if remember_position and last_position is not None:
        
        safe_position = GetSafePosition( last_position )
        
        tlw.SetPosition( safe_position )
        
    elif default_position == 'topleft':
        
        if parent is not None:
            
            if isinstance( parent, wx.TopLevelWindow ):
                
                parent_tlp = parent
                
            else:
                
                parent_tlp = parent.GetTopLevelParent()
                
            
            ( parent_x, parent_y ) = parent_tlp.GetPositionTuple()
            
            tlw.SetPosition( ( parent_x + CHILD_POSITION_PADDING, parent_y + CHILD_POSITION_PADDING ) )
            
        else:
            
            safe_position = GetSafePosition( ( 0 + CHILD_POSITION_PADDING, 0 + CHILD_POSITION_PADDING ) )
            
            tlw.SetPosition( safe_position )
            
        
    elif default_position == 'center':
        
        wx.CallAfter( tlw.Center )
        
    
    # if these aren't callafter, the size and pos calls don't stick if a restore event happens
    
    if maximised:
        
        wx.CallAfter( tlw.Maximize )
        
    
    if fullscreen:
        
        wx.CallAfter( tlw.ShowFullScreen, True, wx.FULLSCREEN_ALL )
        
    
class NewDialog( wx.Dialog ):
    
    def __init__( self, parent, title ):
        
        style = wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER
        
        if not HC.PLATFORM_LINUX and parent is not None:
            
            style |= wx.FRAME_FLOAT_ON_PARENT
            
        
        wx.Dialog.__init__( self, parent, title = title, style = style )
        
        self._new_options = HydrusGlobals.client_controller.GetNewOptions()
        
        self.SetBackgroundColour( wx.SystemSettings.GetColour( wx.SYS_COLOUR_FRAMEBK ) )
        
        self.SetIcon( wx.Icon( os.path.join( HC.STATIC_DIR, 'hydrus.ico' ), wx.BITMAP_TYPE_ICO ) )
        
        self.Bind( wx.EVT_BUTTON, self.EventDialogButton )
        
        HydrusGlobals.client_controller.ResetIdleTimer()
        
    
    def EventDialogButton( self, event ): self.EndModal( event.GetId() )
    
class DialogThatResizes( NewDialog ):
    
    def __init__( self, parent, title, frame_key ):
        
        self._frame_key = frame_key
        
        NewDialog.__init__( self, parent, title )
        
    
class DialogThatTakesScrollablePanel( DialogThatResizes ):
    
    def __init__( self, parent, title, frame_key ):
        
        self._panel = None
        
        DialogThatResizes.__init__( self, parent, title, frame_key )
        
        self._apply = wx.Button( self, id = wx.ID_OK, label = 'apply' )
        self._apply.Bind( wx.EVT_BUTTON, self.EventOk )
        self._apply.SetForegroundColour( ( 0, 128, 0 ) )
        
        self._cancel = wx.Button( self, id = wx.ID_CANCEL, label = 'cancel' )
        self._cancel.SetForegroundColour( ( 128, 0, 0 ) )
        
        self.Bind( wx.EVT_MENU, self.EventMenu )
        self.Bind( CC.EVT_SIZE_CHANGED, self.EventChildSizeChanged )
        
    
    def EventChildSizeChanged( self, event ):
        
        if self._panel is not None:
            
            # the min size here is to compensate for wx.Notebook and anything else that don't update virtualsize on page change
            
            ( current_panel_width, current_panel_height ) = self._panel.GetSize()
            ( desired_panel_width, desired_panel_height ) = self._panel.GetVirtualSize()
            ( min_panel_width, min_panel_height ) = self._panel.GetEffectiveMinSize()
            
            desired_delta_width = max( 0, desired_panel_width - current_panel_width, min_panel_width - current_panel_width )
            desired_delta_height = max( 0, desired_panel_height - current_panel_height, min_panel_height - current_panel_height )
            
            if desired_delta_width > 0 or desired_delta_height > 0:
                
                ExpandTLWIfPossible( self, self._frame_key, ( desired_delta_width, desired_delta_height ) )
                
            
        
    
    def EventMenu( self, event ):
        
        action = ClientCaches.MENU_EVENT_ID_TO_ACTION_CACHE.GetAction( event.GetId() )
        
        if action is not None:
            
            ( command, data ) = action
            
            if command == 'ok':
                
                self.EventOk( None )
                
            else:
                
                event.Skip()
                
            
        
    
    def EventOk( self, event ):
        
        raise NotImplementedError()
        
    
    def SetPanel( self, panel ):
        
        self._panel = panel
        
        buttonbox = wx.BoxSizer( wx.HORIZONTAL )
        
        buttonbox.AddF( self._apply, CC.FLAGS_VCENTER )
        buttonbox.AddF( self._cancel, CC.FLAGS_VCENTER )
        
        vbox = wx.BoxSizer( wx.VERTICAL )
        
        vbox.AddF( self._panel, CC.FLAGS_EXPAND_BOTH_WAYS )
        vbox.AddF( buttonbox, CC.FLAGS_BUTTON_SIZER )
        
        self.SetSizer( vbox )
        
        SetTLWSizeAndPosition( self, self._frame_key )
        
        self._panel.SetupScrolling()
        
    
class DialogEdit( DialogThatTakesScrollablePanel ):
    
    def __init__( self, parent, title ):
        
        DialogThatTakesScrollablePanel.__init__( self, parent, title, 'regular_dialog' )
        
    
    def EventOk( self, event ):
        
        SaveTLWSizeAndPosition( self, self._frame_key )
        
        self.EndModal( wx.ID_OK )
        
    
class DialogManage( DialogThatTakesScrollablePanel ):
    
    def EventOk( self, event ):
        
        self._panel.CommitChanges()
        
        SaveTLWSizeAndPosition( self, self._frame_key )
        
        self.EndModal( wx.ID_OK )
        
    
class Frame( wx.Frame ):
    
    def __init__( self, parent, title, float_on_parent = True ):
        
        style = wx.DEFAULT_FRAME_STYLE
        
        if float_on_parent:
            
            style |= wx.FRAME_FLOAT_ON_PARENT
            
        
        wx.Frame.__init__( self, parent, title = title, style = style )
        
        self._new_options = HydrusGlobals.client_controller.GetNewOptions()
        
        self.SetBackgroundColour( wx.SystemSettings.GetColour( wx.SYS_COLOUR_FRAMEBK ) )
        
        self.SetIcon( wx.Icon( os.path.join( HC.STATIC_DIR, 'hydrus.ico' ), wx.BITMAP_TYPE_ICO ) )
        
        HydrusGlobals.client_controller.ResetIdleTimer()
        
    
class FrameThatResizes( Frame ):
    
    def __init__( self, parent, title, frame_key, float_on_parent = True ):
        
        self._frame_key = frame_key
        
        Frame.__init__( self, parent, title, float_on_parent )
        
        self.Bind( wx.EVT_SIZE, self.EventSizeAndPositionChanged )
        self.Bind( wx.EVT_MOVE_END, self.EventSizeAndPositionChanged )
        self.Bind( wx.EVT_CLOSE, self.EventSizeAndPositionChanged )
        self.Bind( wx.EVT_MAXIMIZE, self.EventSizeAndPositionChanged )
        
    
    def EventSizeAndPositionChanged( self, event ):
        
        SaveTLWSizeAndPosition( self, self._frame_key )
        
        event.Skip()
        
    
class FrameThatTakesScrollablePanel( FrameThatResizes ):
    
    def __init__( self, parent, title, frame_key, float_on_parent = True ):
        
        self._panel = None
        
        FrameThatResizes.__init__( self, parent, title, frame_key, float_on_parent )
        
        self._ok = wx.Button( self, id = wx.ID_OK, label = 'close' )
        self._ok.Bind( wx.EVT_BUTTON, self.EventCloseButton )
        
        self.Bind( wx.EVT_MENU, self.EventMenu )
        self.Bind( CC.EVT_SIZE_CHANGED, self.EventChildSizeChanged )
        
    
    def EventMenu( self, event ):
        
        action = ClientCaches.MENU_EVENT_ID_TO_ACTION_CACHE.GetAction( event.GetId() )
        
        if action is not None:
            
            ( command, data ) = action
            
            if command == 'ok':
                
                self.Close()
                
            else:
                
                event.Skip()
                
            
        
    
    def EventCloseButton( self, event ):
        
        self.Close()
        
    
    def EventChildSizeChanged( self, event ):
        
        if self._panel is not None:
            
            # the min size here is to compensate for wx.Notebook and anything else that don't update virtualsize on page change
            
            ( current_panel_width, current_panel_height ) = self._panel.GetSize()
            ( desired_panel_width, desired_panel_height ) = self._panel.GetVirtualSize()
            ( min_panel_width, min_panel_height ) = self._panel.GetEffectiveMinSize()
            
            desired_delta_width = max( 0, desired_panel_width - current_panel_width, min_panel_width - current_panel_width )
            desired_delta_height = max( 0, desired_panel_height - current_panel_height, min_panel_height - current_panel_height )
            
            if desired_delta_width > 0 or desired_delta_height > 0:
                
                ExpandTLWIfPossible( self, self._frame_key, ( desired_delta_width, desired_delta_height ) )
                
            
        
    
    def SetPanel( self, panel ):
        
        self._panel = panel
        
        vbox = wx.BoxSizer( wx.VERTICAL )
        
        vbox.AddF( self._panel, CC.FLAGS_EXPAND_BOTH_WAYS )
        vbox.AddF( self._ok, CC.FLAGS_LONE_BUTTON )
        
        self.SetSizer( vbox )
        
        SetTLWSizeAndPosition( self, self._frame_key )
        
        self.Show( True )
        
        self._panel.SetupScrolling()
        
    
class ShowKeys( Frame ):
    
    def __init__( self, key_type, keys ):
        
        if key_type == 'registration': title = 'Registration Keys'
        elif key_type == 'access': title = 'Access Keys'
        
        # give it no parent, so this doesn't close when the dialog is closed!
        Frame.__init__( self, None, HydrusGlobals.client_controller.PrepStringForDisplay( title ), float_on_parent = False )
        
        self._key_type = key_type
        self._keys = keys
        
        #
        
        self._text_ctrl = wx.TextCtrl( self, style = wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_DONTWRAP )
        
        self._save_to_file = wx.Button( self, label = 'save to file' )
        self._save_to_file.Bind( wx.EVT_BUTTON, self.EventSaveToFile )
        
        self._done = wx.Button( self, label = 'done' )
        self._done.Bind( wx.EVT_BUTTON, self.EventDone )
        
        #
        
        if key_type == 'registration': prepend = 'r'
        else: prepend = ''
        
        self._text = os.linesep.join( [ prepend + key.encode( 'hex' ) for key in self._keys ] )
        
        self._text_ctrl.SetValue( self._text )
        
        #
        
        vbox = wx.BoxSizer( wx.VERTICAL )
        
        vbox.AddF( self._text_ctrl, CC.FLAGS_EXPAND_BOTH_WAYS )
        vbox.AddF( self._save_to_file, CC.FLAGS_LONE_BUTTON )
        vbox.AddF( self._done, CC.FLAGS_LONE_BUTTON )
        
        self.SetSizer( vbox )
        
        ( x, y ) = self.GetEffectiveMinSize()
        
        if x < 500: x = 500
        if y < 200: y = 200
        
        self.SetInitialSize( ( x, y ) )
        
        self.Show( True )
        
    
    def EventDone( self, event ):
        
        self.Close()
        
    
    def EventSaveToFile( self, event ):
        
        filename = 'keys.txt'
        
        with wx.FileDialog( None, style=wx.FD_SAVE, defaultFile = filename ) as dlg:
            
            if dlg.ShowModal() == wx.ID_OK:
                
                path = HydrusData.ToUnicode( dlg.GetPath() )
                
                with open( path, 'wb' ) as f: f.write( HydrusData.ToByteString( self._text ) )
                
            
        
    
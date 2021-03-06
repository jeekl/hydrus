import ClientConstants as CC
import ClientData
import ClientGUICommon
import ClientSearch
import collections
import HydrusConstants as HC
import HydrusGlobals
import wx

class ListBoxTagsSuggestionsFavourites( ClientGUICommon.ListBoxTagsStrings ):
    
    def __init__( self, parent, activate_callable ):
        
        ClientGUICommon.ListBoxTagsStrings.__init__( self, parent )
        
        self._activate_callable = activate_callable
        
    
    def _Activate( self ):
        
        if len( self._selected_terms ) > 0:
            
            tags = set( self._selected_terms )
            
            self._activate_callable( tags )
            
        
    
    def SetTags( self, tags ):
        
        ClientGUICommon.ListBoxTagsStrings.SetTags( self, tags )
        
        width = HydrusGlobals.client_controller.GetNewOptions().GetNoneableInteger( 'suggested_tags_width' )
        
        if width is None:
            
            if len( self._ordered_strings ) > 0:
                
                dc = wx.MemoryDC( self._client_bmp )
                
                dc.SetFont( wx.SystemSettings.GetFont( wx.SYS_DEFAULT_GUI_FONT ) )
                
                width = max( ( dc.GetTextExtent( s )[0] for s in self._ordered_strings ) )
                
                self.SetMinClientSize( ( width + 2 * self.TEXT_X_PADDING, -1 ) )
                
            
        else:
            
            self.SetMinSize( ( width, -1 ) )
            
        
        wx.PostEvent( self.GetParent(), CC.SizeChangedEvent( -1 ) )
        
    
class ListBoxTagsSuggestionsRelated( ClientGUICommon.ListBoxTags ):
    
    def __init__( self, parent, activate_callable ):
        
        ClientGUICommon.ListBoxTags.__init__( self, parent )
        
        self._activate_callable = activate_callable
        
        width = HydrusGlobals.client_controller.GetNewOptions().GetInteger( 'related_tags_width' )
        
        self.SetMinSize( ( 200, -1 ) )
        
    
    def _Activate( self ):
        
        if len( self._selected_terms ) > 0:
            
            tags = { predicate.GetValue() for predicate in self._selected_terms }
            
            self._activate_callable( tags )
            
        
    
    def SetPredicates( self, predicates ):
        
        self._ordered_strings = []
        self._strings_to_terms = {}
        
        for predicate in predicates:
            
            tag_string = predicate.GetValue()
            
            self._ordered_strings.append( tag_string )
            self._strings_to_terms[ tag_string ] = predicate
            
        
        self._TextsHaveChanged()
        
    
class RecentTagsPanel( wx.Panel ):
    
    def __init__( self, parent, service_key, activate_callable, canvas_key = None ):
        
        wx.Panel.__init__( self, parent )
        
        self._service_key = service_key
        self._canvas_key = canvas_key
        
        self._new_options = HydrusGlobals.client_controller.GetNewOptions()
        
        vbox = wx.BoxSizer( wx.VERTICAL )
        
        clear_button = wx.Button( self, label = 'clear' )
        clear_button.Bind( wx.EVT_BUTTON, self.EventClear )
        
        self._recent_tags = ListBoxTagsSuggestionsFavourites( self, activate_callable )
        
        vbox.AddF( clear_button, CC.FLAGS_EXPAND_PERPENDICULAR )
        vbox.AddF( self._recent_tags, CC.FLAGS_EXPAND_BOTH_WAYS )
        
        self.SetSizer( vbox )
        
        self._RefreshRecentTags()
        
        if self._canvas_key is not None:
            
            HydrusGlobals.client_controller.sub( self, 'CanvasHasNewMedia', 'canvas_new_display_media' )
            
        
    
    def _RefreshRecentTags( self ):
        
        recent_tags = HydrusGlobals.client_controller.Read( 'recent_tags', self._service_key )
        
        self._recent_tags.SetTags( recent_tags )
        
    
    def CanvasHasNewMedia( self, canvas_key, new_media_singleton ):
        
        if canvas_key == self._canvas_key:
            
            self._RefreshRecentTags()
            
        
    
    def EventClear( self, event ):
        
        HydrusGlobals.client_controller.WriteSynchronous( 'push_recent_tags', self._service_key, None )
        
        self._RefreshRecentTags()
        
    
class RelatedTagsPanel( wx.Panel ):
    
    def __init__( self, parent, service_key, media, activate_callable, canvas_key = None ):
        
        wx.Panel.__init__( self, parent )
        
        self._service_key = service_key
        self._media = media
        self._canvas_key = canvas_key
        
        self._new_options = HydrusGlobals.client_controller.GetNewOptions()
        
        vbox = wx.BoxSizer( wx.VERTICAL )
        
        button_2 = wx.Button( self, label = 'medium' )
        button_2.Bind( wx.EVT_BUTTON, self.EventSuggestedRelatedTags2 )
        button_2.SetMinSize( ( 30, -1 ) )
        
        button_3 = wx.Button( self, label = 'thorough' )
        button_3.Bind( wx.EVT_BUTTON, self.EventSuggestedRelatedTags3 )
        button_3.SetMinSize( ( 30, -1 ) )
        
        self._related_tags = ListBoxTagsSuggestionsRelated( self, activate_callable )
        
        button_hbox = wx.BoxSizer( wx.HORIZONTAL )
        
        button_hbox.AddF( button_2, CC.FLAGS_EXPAND_SIZER_BOTH_WAYS )
        button_hbox.AddF( button_3, CC.FLAGS_EXPAND_SIZER_BOTH_WAYS )
        
        vbox.AddF( button_hbox, CC.FLAGS_EXPAND_PERPENDICULAR )
        vbox.AddF( self._related_tags, CC.FLAGS_EXPAND_BOTH_WAYS )
        
        self.SetSizer( vbox )
        
        if self._canvas_key is not None:
            
            HydrusGlobals.client_controller.sub( self, 'CanvasHasNewMedia', 'canvas_new_display_media' )
            
        
        self._QuickSuggestedRelatedTags()
        
    
    def _FetchRelatedTags( self, max_time_to_take ):
        
        ( m, ) = self._media
        
        hash = m.GetHash()
        
        ( current_tags_to_count, deleted_tags_to_count, pending_tags_to_count, petitioned_tags_to_count ) = ClientData.GetMediasTagCount( self._media, tag_service_key = self._service_key, collapse_siblings = False )
        
        tags_to_count = collections.Counter()
        
        tags_to_count.update( current_tags_to_count )
        tags_to_count.update( pending_tags_to_count )
        
        search_tags = set( tags_to_count.keys() )
        
        max_results = 100
        
        predicates = HydrusGlobals.client_controller.Read( 'related_tags', self._service_key, hash, search_tags, max_results, max_time_to_take )
        
        predicates = ClientSearch.SortPredicates( predicates )
        
        self._related_tags.SetPredicates( predicates )
        
    
    def _QuickSuggestedRelatedTags( self ):
        
        max_time_to_take = self._new_options.GetInteger( 'related_tags_search_1_duration_ms' ) / 1000.0
        
        self._FetchRelatedTags( max_time_to_take )
        
    
    def CanvasHasNewMedia( self, canvas_key, new_media_singleton ):
        
        if canvas_key == self._canvas_key:
            
            self._media = ( new_media_singleton.Duplicate(), )
            
            self._QuickSuggestedRelatedTags()
            
        
    
    def EventSuggestedRelatedTags2( self, event ):
        
        max_time_to_take = self._new_options.GetInteger( 'related_tags_search_2_duration_ms' ) / 1000.0
        
        self._FetchRelatedTags( max_time_to_take )
        
    
    def EventSuggestedRelatedTags3( self, event ):
        
        max_time_to_take = self._new_options.GetInteger( 'related_tags_search_3_duration_ms' ) / 1000.0
        
        self._FetchRelatedTags( max_time_to_take )
        
    
class SuggestedTagsPanel( wx.Panel ):
    
    def __init__( self, parent, service_key, media, activate_callable, canvas_key = None ):
        
        wx.Panel.__init__( self, parent )
        
        self._service_key = service_key
        self._media = media
        self._canvas_key = canvas_key
        
        self._new_options = HydrusGlobals.client_controller.GetNewOptions()
        
        something_to_show = False
        
        hbox = wx.BoxSizer( wx.HORIZONTAL )
        
        favourites = self._new_options.GetSuggestedTagsFavourites( service_key )
        
        if len( favourites ) > 0:
            
            favourite_tags = ListBoxTagsSuggestionsFavourites( self, activate_callable )
            
            favourite_tags.SetTags( favourites )
            
            hbox.AddF( favourite_tags, CC.FLAGS_EXPAND_PERPENDICULAR )
            
            something_to_show = True
            
        
        if self._new_options.GetBoolean( 'show_related_tags' ) and len( media ) == 1:
            
            related_tags = RelatedTagsPanel( self, service_key, media, activate_callable, canvas_key = self._canvas_key )
            
            hbox.AddF( related_tags, CC.FLAGS_EXPAND_BOTH_WAYS )
            
            something_to_show = True
            
        
        if self._new_options.GetNoneableInteger( 'num_recent_tags' ) is not None:
            
            recent_tags = RecentTagsPanel( self, service_key, activate_callable, canvas_key = self._canvas_key )
            
            hbox.AddF( recent_tags, CC.FLAGS_EXPAND_PERPENDICULAR )
            
            something_to_show = True
            
        
        self.SetSizer( hbox )
        
        if not something_to_show:
            
            self.Hide()
            
        
    
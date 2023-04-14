using RazorEnhanced;
using static RazorEnhanced.Items;
using System;
using System.Collections.Generic;
using System.Linq;

namespace RazorEnhancedUOAlive
{
    internal class DurabilityWatcher
    {
        private const int CHECK_DELAY = 15; //How many seconds between durability checks?
        private const double BEGIN_WARNING = 0.5; //Durability %%PERCENT%% remaining before getting a warning message
        private const ushort LINE_RED = 0x0805;
        private const ushort LINE_BLUE = 0x0806;
        private const ushort LINE_GREEN = 0x0808;
        private const ushort LINE_YELLOW = 0x0809;
        private const string SHAREDLAYERNAME = "CheckLayers";
        private const string SHARED_LAYERS_CONFIG_OPEN = "LayersConfigOpen";
        private string[] LAYERS_TO_CHECK = new string[] {"RightHand", "LeftHand", "Shoes", "Pants", "Shirt", "Head", "Gloves", "Ring", "Neck", "Waist", "InnerTorso",
                 "Bracelet", "MiddleTorso", "Earrings", "Arms", "Cloak", "OuterTorso", "OuterLegs", "InnerLegs", "Talisman"};

        public void Run()
        {
            if (!Misc.CheckSharedValue(SHAREDLAYERNAME)){
                Misc.SetSharedValue(SHAREDLAYERNAME,LAYERS_TO_CHECK);
            }
            if (!Misc.CheckSharedValue(SHARED_LAYERS_CONFIG_OPEN)){
                Misc.SetSharedValue(SHARED_LAYERS_CONFIG_OPEN,false);
            }
            SetupGump();
        }
        private void SetupGump(){
            var layers     = (string[])Misc.ReadSharedValue(SHAREDLAYERNAME);
            var itemFilter = new Filter() { Enabled = true };
            itemFilter.Layers.AddRange(layers);
            
            var items      = layers.Length > 0 ? ApplyFilter(itemFilter) : new List<Item>();
            items          = items.Where(i => i.Container == Player.Serial  && i.MaxDurability > 0).ToList();
            int gumpId     = 987654;
            var gd         = Gumps.CreateGump();
            var itemHeight = 18;
            var height     = (items.Count * itemHeight * 2) + (itemHeight * 2) + (items.Count == 0 ? 30 : 0);
            var width      = 250;
            Gumps.AddPage(ref gd, 0);
            Gumps.AddBackground(ref gd,0,0,width,height,gumpId);
            Gumps.AddAlphaRegion(ref gd,0,0,width,height);
            Gumps.AddHtml(ref gd, 0,0, width, height,"",false,false);
            Gumps.AddLabel(ref gd, 0, 0, 88, "Equipment Durability");
            Gumps.AddButton(ref gd, width - 70,0, 0xFBF,0xFBE,1,1,0);
            Gumps.AddButton(ref gd, width - 30,0, 0xFB1,0xFB2,0,1,0);
            
            var startX       = 5;
            var startY       = 25;
            var baseBarWidth = 106;
            if (items.Count == 0){
                 Gumps.AddLabel(ref gd, startX, startY, 334, "No Layers configured to observe");
            }
            foreach (Item i in items) {
                 double durPercentage = (double)i.Durability / (double)i.MaxDurability;
                 
                 Gumps.AddLabel(ref gd, startX, startY, 88, i.Name);
                 startY += itemHeight;
                 Gumps.AddImage(ref gd, startX, startY, LINE_RED);
                 ushort statusId = LINE_GREEN;
                 if (durPercentage >= .9){
                     statusId = LINE_BLUE;
                 } 
                 if (durPercentage <= BEGIN_WARNING){
                     statusId = LINE_YELLOW;
                 }
                 Gumps.AddImageTiled(ref gd, startX, startY, (int)Math.Floor(baseBarWidth * durPercentage),12,statusId);
                 Gumps.AddLabel(ref gd, width - 80, startY - 5, 88, $"{i.Durability} / {i.MaxDurability}");
                 
                 startY += itemHeight;
            }
            Gumps.SendGump((uint)gumpId, (uint)Player.Serial, 50, 50, gd.gumpDefinition, gd.gumpStrings);
            var g_data = Gumps.GetGumpData((uint)gumpId);
            if ((bool)Misc.ReadSharedValue(SHARED_LAYERS_CONFIG_OPEN)){
                var l_g_data = LayerGump(g_data.x, g_data.y);
                if (l_g_data.buttonid == 1){
                    var newLayers = LAYERS_TO_CHECK.ToList().Where((l,i) => l_g_data.switches.Contains(i)).ToList();
                    Misc.SetSharedValue(SHAREDLAYERNAME,newLayers.ToArray());
                    Misc.SetSharedValue(SHARED_LAYERS_CONFIG_OPEN,false);
                    SetupGump();
                }
            }
            Timer.Create("SetupGump_GetActions", CHECK_DELAY * 1000);
            while (!g_data.hasResponse){
                Misc.Pause(500);
                g_data = Gumps.GetGumpData((uint)gumpId);
                if (!Timer.Check("SetupGump_GetActions")){
                    break;
                }
            }
           if (!Timer.Check("SetupGump_GetActions")){
                SetupGump();
                return;
           }
            
            if (g_data.buttonid == 0)
                Gumps.CloseGump((uint)gumpId);
            if (g_data.buttonid == 1){
                Misc.SetSharedValue(SHARED_LAYERS_CONFIG_OPEN,true);
                SetupGump();
             }
                
        }
        private Gumps.GumpData LayerGump(uint x, uint y){
            int gumpId = 987653;
            var gd     = Gumps.CreateGump();
            var height = (LAYERS_TO_CHECK.Length / 4) * 25 + 70;
            var width  = 450;
            Gumps.AddPage(ref gd, 0);
            Gumps.AddBackground(ref gd,0,0,width,height,gumpId);
            Gumps.AddAlphaRegion(ref gd,0,0,width,height);
            Gumps.AddHtml(ref gd, 0,0, width, height,"",false,false);
            var startX = 5;
            var startY = 10;
            var i      = 1;
            var layers = (string[])Misc.ReadSharedValue(SHAREDLAYERNAME);
            foreach(var layer in LAYERS_TO_CHECK){
                var isChecked = layers.Contains(layer);
                Gumps.AddCheck(ref gd, startX, startY, 0x867,0x869,isChecked,i - 1);
                Gumps.AddLabel(ref gd, startX + 35, startY + 5, 88, layer);
                startX += 115;
                if (i % 4 == 0){
                    startY += 25;
                    startX = 5;
                }
                i++;
            }
            Gumps.AddButton(ref gd, width - 80,height - 30, 0x850,0x851,1,1,0);
            Gumps.SendGump((uint)gumpId, (uint)Player.Serial, x, y, gd.gumpDefinition, gd.gumpStrings);
            var l_g_data = Gumps.GetGumpData((uint)gumpId);
            Misc.SetSharedValue(SHARED_LAYERS_CONFIG_OPEN,false);
            while (!l_g_data.hasResponse){
                Misc.Pause(500);
            }
            return l_g_data;
        }
    }
}
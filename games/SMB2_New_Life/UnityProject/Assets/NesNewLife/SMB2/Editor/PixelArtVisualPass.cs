#if UNITY_EDITOR
using System;
using System.Collections.Generic;
using System.IO;
using UnityEditor;
using UnityEngine;

namespace NesNewLife.SMB2.EditorTools
{
    /// <summary>
    /// Generates an original/public-safe pixel-art pack and applies it to the generated SMB2 New Life scenes.
    /// This deliberately replaces the old single white PrototypeSquare placeholder.
    /// No Nintendo ROM data, ripped sprites, or commercial art is used.
    /// </summary>
    public static class PixelArtVisualPass
    {
        private const string AssetRoot = "Assets/NesNewLife/SMB2/Generated/PixelArt";
        private static readonly Dictionary<string, Sprite> Sprites = new Dictionary<string, Sprite>();
        private static bool prepared;

        [MenuItem("NES New Life/SMB2/Apply Pixel Art Visual Pass")]
        public static void ApplyCurrentScene()
        {
            EnsureSprites();

            foreach (SpriteRenderer renderer in UnityEngine.Object.FindObjectsByType<SpriteRenderer>(FindObjectsSortMode.None))
            {
                Sprite sprite = ResolveSprite(renderer.gameObject.name);
                if (sprite == null)
                    continue;

                renderer.sprite = sprite;
                renderer.textureMode = SpriteMaskInteraction.None;

                if (UsesFullColor(renderer.gameObject.name))
                    renderer.color = Color.white;
            }

            AddDecorIfMissing();
            Debug.Log("NES New Life: original pixel-art visual pass applied.");
        }

        private static void EnsureSprites()
        {
            if (prepared)
                return;

            Directory.CreateDirectory(AssetRoot);

            Make("Hero", DrawHero);
            Make("Enemy", DrawEnemy);
            Make("Boss", DrawBoss);
            Make("Carryable", DrawCarryable);
            Make("Plant", DrawPlant);
            Make("Key", DrawKey);
            Make("Door", DrawDoor);
            Make("Pickup", DrawPickup);
            Make("Heart", DrawHeart);
            Make("Checkpoint", DrawCheckpoint);
            Make("Exit", DrawExit);
            Make("Ground", DrawGround);
            Make("Platform", DrawPlatform);
            Make("Barrier", DrawBarrier);
            Make("Backdrop", DrawBackdrop);
            Make("Vine", DrawVine);
            Make("Spikes", DrawSpikes);
            Make("Landmark", DrawLandmark);
            Make("Cloud", DrawCloud);
            Make("Shrub", DrawShrub);
            Make("Moon", DrawMoon);

            AssetDatabase.SaveAssets();
            AssetDatabase.Refresh(ImportAssetOptions.ForceSynchronousImport);
            prepared = true;
        }

        private static void Make(string name, Action<Texture2D> painter)
        {
            string path = AssetRoot + "/" + name + ".png";
            Texture2D tex = new Texture2D(16, 16, TextureFormat.RGBA32, false);
            tex.filterMode = FilterMode.Point;
            Clear(tex);
            painter(tex);
            tex.Apply();
            File.WriteAllBytes(path, tex.EncodeToPNG());
            UnityEngine.Object.DestroyImmediate(tex);

            AssetDatabase.ImportAsset(path, ImportAssetOptions.ForceSynchronousImport | ImportAssetOptions.ForceUpdate);
            TextureImporter importer = AssetImporter.GetAtPath(path) as TextureImporter;
            if (importer == null)
                throw new Exception("Could not configure generated pixel art: " + path);

            importer.textureType = TextureImporterType.Sprite;
            importer.spriteImportMode = SpriteImportMode.Single;
            importer.spritePixelsPerUnit = 16f;
            importer.filterMode = FilterMode.Point;
            importer.mipmapEnabled = false;
            importer.alphaIsTransparency = true;
            importer.textureCompression = TextureImporterCompression.Uncompressed;
            importer.wrapMode = TextureWrapMode.Clamp;
            importer.SaveAndReimport();

            Sprite sprite = AssetDatabase.LoadAssetAtPath<Sprite>(path);
            if (sprite == null)
                throw new Exception("Generated pixel art was not imported as Sprite: " + path);
            Sprites[name] = sprite;
        }

        private static Sprite ResolveSprite(string objectName)
        {
            if (objectName == "Player") return Sprites["Hero"];
            if (objectName.Contains("Enemy_Patroller")) return Sprites["Enemy"];
            if (objectName.Contains("MINIBOSS") || objectName.Contains("Guardian")) return Sprites["Boss"];
            if (objectName.Contains("Pullable_Plant")) return Sprites["Plant"];
            if (objectName.Contains("Carryable") || objectName.Contains("Pulled_Item")) return Sprites["Carryable"];
            if (objectName == "KEY") return Sprites["Key"];
            if (objectName.Contains("Door_")) return Sprites["Door"];
            if (objectName.Contains("ScorePickup")) return Sprites["Pickup"];
            if (objectName == "Heart") return Sprites["Heart"];
            if (objectName == "Checkpoint") return Sprites["Checkpoint"];
            if (objectName.Contains("LEVEL EXIT")) return Sprites["Exit"];
            if (objectName.Contains("Spike Hazard")) return Sprites["Spikes"];
            if (objectName.Contains("Climbable Vine")) return Sprites["Vine"];
            if (objectName.Contains("World ") && objectName.Contains("Landmark")) return Sprites["Landmark"];
            if (objectName == "Ground") return Sprites["Ground"];
            if (objectName.Contains("Platform") || objectName.Contains("Vertical Ledge")) return Sprites["Platform"];
            if (objectName.Contains("World Barrier")) return Sprites["Barrier"];
            if (objectName.Contains("Backdrop")) return Sprites["Backdrop"];
            return null;
        }

        private static bool UsesFullColor(string objectName)
        {
            return objectName == "Player" ||
                   objectName.Contains("Enemy_Patroller") ||
                   objectName.Contains("MINIBOSS") ||
                   objectName.Contains("Guardian") ||
                   objectName.Contains("Pullable_Plant") ||
                   objectName.Contains("Carryable") ||
                   objectName.Contains("Pulled_Item") ||
                   objectName == "KEY" ||
                   objectName.Contains("Door_") ||
                   objectName.Contains("ScorePickup") ||
                   objectName == "Heart" ||
                   objectName == "Checkpoint" ||
                   objectName.Contains("LEVEL EXIT") ||
                   objectName.Contains("Spike Hazard") ||
                   objectName.Contains("Climbable Vine");
        }

        private static void AddDecorIfMissing()
        {
            if (GameObject.Find("Pixel Art Decor") != null)
                return;

            GameObject root = new GameObject("Pixel Art Decor");
            CreateDecor(root.transform, "Moon", new Vector2(-17f, 3.5f), new Vector2(2.2f, 2.2f), Sprites["Moon"], -18);
            CreateDecor(root.transform, "Cloud A", new Vector2(-8f, 2.8f), new Vector2(3.2f, 1.4f), Sprites["Cloud"], -17);
            CreateDecor(root.transform, "Cloud B", new Vector2(17f, 3.4f), new Vector2(4.0f, 1.6f), Sprites["Cloud"], -17);
            CreateDecor(root.transform, "Cloud C", new Vector2(43f, 2.4f), new Vector2(3.4f, 1.4f), Sprites["Cloud"], -17);

            for (int i = 0; i < 7; i++)
            {
                float x = -20f + i * 12f;
                CreateDecor(root.transform, "Shrub " + i, new Vector2(x, -1.75f), new Vector2(1.8f, 1.0f), Sprites["Shrub"], -3);
            }

            CreateDecor(root.transform, "Underground Crystal A", new Vector2(12f, -18.8f), new Vector2(1.1f, 1.7f), Sprites["Landmark"], -4, new Color(0.35f, 0.72f, 0.95f));
            CreateDecor(root.transform, "Underground Crystal B", new Vector2(25f, -18.8f), new Vector2(1.1f, 1.7f), Sprites["Landmark"], -4, new Color(0.72f, 0.42f, 0.95f));
        }

        private static void CreateDecor(Transform parent, string name, Vector2 position, Vector2 scale, Sprite sprite, int order, Color? tint = null)
        {
            GameObject obj = new GameObject(name);
            obj.transform.SetParent(parent);
            obj.transform.position = position;
            obj.transform.localScale = new Vector3(scale.x, scale.y, 1f);
            SpriteRenderer renderer = obj.AddComponent<SpriteRenderer>();
            renderer.sprite = sprite;
            renderer.sortingOrder = order;
            renderer.color = tint ?? Color.white;
        }

        private static void Clear(Texture2D tex)
        {
            Color32[] pixels = new Color32[16 * 16];
            for (int i = 0; i < pixels.Length; i++)
                pixels[i] = new Color32(0, 0, 0, 0);
            tex.SetPixels32(pixels);
        }

        private static void Rect(Texture2D t, int x, int y, int w, int h, Color c)
        {
            for (int yy = y; yy < y + h; yy++)
                for (int xx = x; xx < x + w; xx++)
                    if (xx >= 0 && xx < 16 && yy >= 0 && yy < 16)
                        t.SetPixel(xx, yy, c);
        }

        private static void Pixel(Texture2D t, int x, int y, Color c)
        {
            if (x >= 0 && x < 16 && y >= 0 && y < 16)
                t.SetPixel(x, y, c);
        }

        private static readonly Color Ink = new Color32(28, 24, 40, 255);
        private static readonly Color Light = new Color32(244, 236, 210, 255);

        private static void DrawHero(Texture2D t)
        {
            Color skin = new Color32(231, 165, 104, 255);
            Color hood = new Color32(55, 201, 196, 255);
            Color coat = new Color32(177, 53, 86, 255);
            Color boot = new Color32(77, 48, 50, 255);
            Rect(t, 5, 12, 6, 2, Ink); Rect(t, 4, 10, 8, 3, hood);
            Rect(t, 5, 7, 6, 4, skin); Pixel(t, 6, 9, Ink); Pixel(t, 9, 9, Ink);
            Rect(t, 4, 4, 8, 4, Ink); Rect(t, 5, 4, 6, 4, coat);
            Rect(t, 3, 5, 2, 2, skin); Rect(t, 11, 5, 2, 2, skin);
            Rect(t, 5, 1, 2, 3, boot); Rect(t, 9, 1, 2, 3, boot);
            Pixel(t, 4, 12, hood); Pixel(t, 11, 12, hood); Pixel(t, 7, 6, Light);
        }

        private static void DrawEnemy(Texture2D t)
        {
            Color body = new Color32(216, 76, 61, 255);
            Color belly = new Color32(247, 173, 84, 255);
            Pixel(t, 4, 13, Ink); Pixel(t, 11, 13, Ink);
            Rect(t, 3, 5, 10, 8, Ink); Rect(t, 4, 5, 8, 7, body);
            Rect(t, 5, 5, 6, 3, belly); Pixel(t, 6, 9, Light); Pixel(t, 9, 9, Light);
            Pixel(t, 6, 9, Light); Pixel(t, 9, 9, Light); Pixel(t, 6, 8, Ink); Pixel(t, 9, 8, Ink);
            Rect(t, 3, 3, 3, 2, Ink); Rect(t, 10, 3, 3, 2, Ink);
        }

        private static void DrawBoss(Texture2D t)
        {
            Color body = new Color32(131, 56, 179, 255);
            Color armor = new Color32(216, 77, 154, 255);
            Rect(t, 2, 3, 12, 10, Ink); Rect(t, 3, 4, 10, 8, body);
            Rect(t, 5, 2, 2, 3, Ink); Rect(t, 9, 2, 2, 3, Ink);
            Rect(t, 4, 4, 8, 3, armor); Rect(t, 5, 8, 2, 2, Light); Rect(t, 9, 8, 2, 2, Light);
            Pixel(t, 6, 8, Ink); Pixel(t, 10, 8, Ink); Rect(t, 6, 5, 4, 1, Ink);
            Rect(t, 1, 4, 2, 4, body); Rect(t, 13, 4, 2, 4, body);
        }

        private static void DrawCarryable(Texture2D t)
        {
            Color a = new Color32(244, 159, 55, 255);
            Color b = new Color32(126, 74, 57, 255);
            Rect(t, 4, 4, 8, 8, Ink); Rect(t, 5, 5, 6, 6, a);
            Rect(t, 6, 10, 4, 2, new Color32(88, 186, 91, 255));
            Rect(t, 6, 3, 4, 2, b); Pixel(t, 7, 7, Light); Pixel(t, 10, 7, Ink);
        }

        private static void DrawPlant(Texture2D t)
        {
            Color green = new Color32(54, 181, 82, 255);
            Color pink = new Color32(235, 83, 118, 255);
            Rect(t, 7, 2, 2, 8, green); Rect(t, 5, 8, 6, 4, Ink); Rect(t, 6, 9, 4, 3, pink);
            Rect(t, 4, 6, 3, 2, green); Rect(t, 9, 5, 3, 2, green); Pixel(t, 7, 10, Light); Pixel(t, 9, 10, Light);
        }

        private static void DrawKey(Texture2D t)
        {
            Color gold = new Color32(247, 202, 61, 255);
            Rect(t, 3, 9, 7, 5, Ink); Rect(t, 4, 10, 5, 3, gold); Rect(t, 7, 3, 2, 8, Ink); Rect(t, 7, 4, 1, 6, gold);
            Rect(t, 8, 3, 4, 2, gold); Rect(t, 10, 5, 2, 2, gold); Rect(t, 5, 11, 2, 1, Ink);
        }

        private static void DrawDoor(Texture2D t)
        {
            Color wood = new Color32(113, 68, 86, 255);
            Color trim = new Color32(224, 163, 72, 255);
            Rect(t, 3, 1, 10, 14, Ink); Rect(t, 4, 2, 8, 12, wood); Rect(t, 5, 11, 6, 2, trim);
            Rect(t, 5, 3, 1, 8, trim); Rect(t, 10, 3, 1, 8, trim); Pixel(t, 9, 7, Light); Pixel(t, 10, 7, Ink);
        }

        private static void DrawPickup(Texture2D t)
        {
            Color gold = new Color32(255, 213, 68, 255);
            Pixel(t, 8, 13, gold); Rect(t, 7, 10, 3, 3, gold); Rect(t, 4, 7, 9, 3, gold); Rect(t, 6, 4, 5, 3, gold);
            Pixel(t, 8, 3, gold); Pixel(t, 8, 8, Light);
        }

        private static void DrawHeart(Texture2D t)
        {
            Color red = new Color32(240, 56, 88, 255);
            Rect(t, 3, 9, 4, 4, red); Rect(t, 9, 9, 4, 4, red); Rect(t, 5, 6, 6, 6, red);
            Rect(t, 6, 4, 4, 3, red); Pixel(t, 7, 3, red); Pixel(t, 8, 3, red); Pixel(t, 5, 11, Light);
        }

        private static void DrawCheckpoint(Texture2D t)
        {
            Color pole = new Color32(222, 213, 188, 255);
            Color flag = new Color32(59, 164, 235, 255);
            Rect(t, 4, 1, 2, 14, pole); Rect(t, 6, 10, 7, 4, Ink); Rect(t, 6, 11, 6, 2, flag); Rect(t, 2, 1, 6, 2, Ink);
        }

        private static void DrawExit(Texture2D t)
        {
            Color cyan = new Color32(61, 225, 198, 255);
            Color blue = new Color32(69, 104, 232, 255);
            Rect(t, 2, 2, 12, 12, Ink); Rect(t, 3, 3, 10, 10, cyan); Rect(t, 5, 5, 6, 6, blue);
            Rect(t, 7, 7, 2, 2, Light); Pixel(t, 3, 12, Light); Pixel(t, 12, 3, Light);
        }

        private static void DrawGround(Texture2D t)
        {
            Rect(t, 0, 0, 16, 16, new Color32(190, 190, 200, 255));
            Rect(t, 0, 12, 16, 4, new Color32(238, 238, 242, 255));
            for (int x = 0; x < 16; x += 4) { Rect(t, x, 10, 2, 2, new Color32(130, 130, 145, 255)); }
            Pixel(t, 3, 5, new Color32(120, 120, 136, 255)); Pixel(t, 11, 3, new Color32(120, 120, 136, 255));
        }

        private static void DrawPlatform(Texture2D t)
        {
            Rect(t, 0, 0, 16, 16, new Color32(205, 205, 214, 255));
            Rect(t, 0, 12, 16, 4, new Color32(245, 245, 248, 255));
            for (int y = 2; y < 12; y += 4) { Rect(t, 0, y, 16, 1, new Color32(135, 135, 150, 255)); }
            for (int x = 4; x < 16; x += 8) { Rect(t, x, 2, 1, 4, new Color32(135, 135, 150, 255)); Rect(t, x + 4, 6, 1, 4, new Color32(135, 135, 150, 255)); }
        }

        private static void DrawBarrier(Texture2D t)
        {
            Rect(t, 0, 0, 16, 16, new Color32(110, 110, 126, 255));
            for (int y = 0; y < 16; y += 4) Rect(t, 0, y, 16, 1, new Color32(62, 62, 78, 255));
            for (int x = 2; x < 16; x += 5) Rect(t, x, 0, 1, 16, new Color32(156, 156, 168, 255));
        }

        private static void DrawBackdrop(Texture2D t)
        {
            Rect(t, 0, 0, 16, 16, new Color32(140, 140, 155, 255));
            Rect(t, 0, 0, 16, 5, new Color32(95, 95, 112, 255));
            for (int x = 1; x < 16; x += 5) { Rect(t, x, 5 + (x % 3), 3, 6, new Color32(175, 175, 188, 255)); }
            Pixel(t, 3, 13, new Color32(225, 225, 232, 255)); Pixel(t, 12, 11, new Color32(225, 225, 232, 255));
        }

        private static void DrawVine(Texture2D t)
        {
            Color green = new Color32(53, 181, 91, 255);
            Rect(t, 7, 0, 2, 16, green); Rect(t, 4, 4, 3, 2, green); Rect(t, 9, 8, 3, 2, green); Rect(t, 4, 12, 3, 2, green);
        }

        private static void DrawSpikes(Texture2D t)
        {
            Color steel = new Color32(226, 231, 237, 255);
            Rect(t, 0, 1, 16, 3, Ink);
            for (int x = 1; x < 16; x += 4) { Pixel(t, x, 4, steel); Rect(t, x + 1, 4, 2, 4, steel); Rect(t, x + 2, 8, 1, 3, steel); }
        }

        private static void DrawLandmark(Texture2D t)
        {
            Rect(t, 7, 1, 2, 14, new Color32(220, 220, 230, 255));
            Rect(t, 5, 3, 6, 8, new Color32(165, 165, 185, 255));
            Rect(t, 3, 5, 10, 4, new Color32(205, 205, 218, 255));
            Pixel(t, 7, 8, Light); Pixel(t, 8, 8, Light);
        }

        private static void DrawCloud(Texture2D t)
        {
            Color c = new Color32(236, 239, 247, 220);
            Rect(t, 2, 5, 12, 5, c); Rect(t, 4, 9, 5, 3, c); Rect(t, 8, 8, 5, 4, c);
        }

        private static void DrawShrub(Texture2D t)
        {
            Color dark = new Color32(36, 112, 88, 255);
            Color green = new Color32(58, 170, 106, 255);
            Rect(t, 2, 2, 12, 5, dark); Rect(t, 3, 4, 10, 5, green); Rect(t, 5, 8, 6, 3, green);
            Pixel(t, 5, 6, new Color32(240, 190, 73, 255)); Pixel(t, 10, 5, new Color32(234, 98, 130, 255));
        }

        private static void DrawMoon(Texture2D t)
        {
            Color moon = new Color32(240, 220, 147, 255);
            Rect(t, 4, 3, 8, 10, moon); Rect(t, 2, 5, 12, 6, moon);
            Rect(t, 8, 7, 5, 5, new Color32(202, 181, 119, 255));
        }
    }
}
#endif

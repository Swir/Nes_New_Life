#if UNITY_EDITOR
using System;
using System.IO;
using UnityEditor;
using UnityEditor.Build.Reporting;
using UnityEngine;

namespace NesNewLife.SMB2.EditorTools
{
    public static class CIBuild
    {
        private const string PrototypeSpritePath = "Assets/NesNewLife/SMB2/Generated/PrototypeSquare.png";

        public static void BuildWindows()
        {
            string projectRoot = Directory.GetParent(Application.dataPath)?.FullName
                ?? throw new Exception("Could not resolve Unity project root.");
            string buildFolder = Path.Combine(projectRoot, "build", "StandaloneWindows64");
            string exePath = Path.Combine(buildFolder, "NES_New_Life_SMB2.exe");

            Debug.Log("[NES New Life CI] Project root: " + projectRoot);
            Debug.Log("[NES New Life CI] Preparing SMB2 Windows x64 release build...");
            Directory.CreateDirectory(buildFolder);

            PreparePrototypeSprite(projectRoot);

            if (!CampaignScenesExist())
            {
                Debug.Log($"[NES New Life CI] Campaign scenes missing. Generating {CampaignCatalog.StageCount} stages...");
                CreateCampaignScenes.Create();
                AssetDatabase.Refresh(ImportAssetOptions.ForceSynchronousImport);
            }

            if (!CampaignScenesExist())
                throw new Exception("Campaign generation failed: one or more stage scenes are missing.");

            if (!ValidateCampaign.ValidateForBuild())
                throw new Exception("Campaign structural validation failed. CI build aborted.");

            string version = ResolveVersion(projectRoot);
            ConfigurePlayer(version);

            var options = new BuildPlayerOptions
            {
                scenes = CreateCampaignScenes.StagePaths,
                locationPathName = exePath,
                target = BuildTarget.StandaloneWindows64,
                options = BuildOptions.CompressWithLz4HC
            };

            BuildReport report = BuildPipeline.BuildPlayer(options);
            BuildSummary summary = report.summary;
            Debug.Log($"[NES New Life CI] Build result={summary.result}, size={summary.totalSize}, time={summary.totalTime}");

            if (summary.result != BuildResult.Succeeded)
                throw new Exception("NES New Life SMB2 Windows build failed: " + summary.result);

            string info =
                "NES NEW LIFE #001 - SMB2 NEW LIFE\n" +
                "Version: " + version + "\n" +
                "Unity: " + Application.unityVersion + "\n" +
                "Target: Windows x64\n" +
                "Campaign slots: " + CampaignCatalog.StageCount + "\n" +
                "Status: alpha development build; original/public-safe placeholder content only.\n";
            File.WriteAllText(Path.Combine(buildFolder, "BUILD_INFO.txt"), info);

            Debug.Log("[NES New Life CI] Windows executable created at: " + exePath);
        }

        private static void PreparePrototypeSprite(string projectRoot)
        {
            string absolutePath = Path.Combine(projectRoot, PrototypeSpritePath.Replace('/', Path.DirectorySeparatorChar));
            string directory = Path.GetDirectoryName(absolutePath);
            if (!string.IsNullOrEmpty(directory))
                Directory.CreateDirectory(directory);

            if (!File.Exists(absolutePath))
            {
                Texture2D texture = new Texture2D(16, 16, TextureFormat.RGBA32, false);
                Color[] pixels = new Color[16 * 16];
                for (int i = 0; i < pixels.Length; i++)
                    pixels[i] = Color.white;
                texture.SetPixels(pixels);
                texture.Apply();
                File.WriteAllBytes(absolutePath, texture.EncodeToPNG());
                UnityEngine.Object.DestroyImmediate(texture);
            }

            AssetDatabase.ImportAsset(
                PrototypeSpritePath,
                ImportAssetOptions.ForceSynchronousImport | ImportAssetOptions.ForceUpdate);

            TextureImporter importer = AssetImporter.GetAtPath(PrototypeSpritePath) as TextureImporter;
            if (importer == null)
                throw new Exception("Prototype sprite importer was not created for " + PrototypeSpritePath);

            importer.textureType = TextureImporterType.Sprite;
            importer.spriteImportMode = SpriteImportMode.Single;
            importer.spritePixelsPerUnit = 16f;
            importer.mipmapEnabled = false;
            importer.alphaIsTransparency = true;
            importer.filterMode = FilterMode.Point;
            importer.textureCompression = TextureImporterCompression.Uncompressed;
            importer.wrapMode = TextureWrapMode.Clamp;
            importer.npotScale = TextureImporterNPOTScale.None;
            importer.SaveAndReimport();

            AssetDatabase.ImportAsset(
                PrototypeSpritePath,
                ImportAssetOptions.ForceSynchronousImport | ImportAssetOptions.ForceUpdate);

            Sprite sprite = AssetDatabase.LoadAssetAtPath<Sprite>(PrototypeSpritePath);
            if (sprite == null)
            {
                UnityEngine.Object[] assets = AssetDatabase.LoadAllAssetsAtPath(PrototypeSpritePath);
                foreach (UnityEngine.Object asset in assets)
                {
                    sprite = asset as Sprite;
                    if (sprite != null)
                        break;
                }
            }

            if (sprite == null)
                throw new Exception("Prototype PNG exists but Unity did not import it as a Sprite.");

            Debug.Log("[NES New Life CI] Prototype sprite prepared successfully: " + PrototypeSpritePath);
        }

        private static bool CampaignScenesExist()
        {
            foreach (string path in CreateCampaignScenes.StagePaths)
            {
                if (!File.Exists(path))
                    return false;
            }
            return true;
        }

        private static void ConfigurePlayer(string version)
        {
            PlayerSettings.companyName = "SWIR Games";
            PlayerSettings.productName = "NES New Life - SMB2 New Life";
            PlayerSettings.bundleVersion = version;
            PlayerSettings.defaultScreenWidth = 1280;
            PlayerSettings.defaultScreenHeight = 720;
            PlayerSettings.fullScreenMode = FullScreenMode.Windowed;
            PlayerSettings.resizableWindow = true;
            PlayerSettings.runInBackground = false;

#pragma warning disable CS0618
            PlayerSettings.SetScriptingBackend(BuildTargetGroup.Standalone, ScriptingImplementation.Mono2x);
#pragma warning restore CS0618
        }

        private static string ResolveVersion(string projectRoot)
        {
            string versionFile = Path.Combine(projectRoot, "VERSION");
            if (!File.Exists(versionFile))
                return "0.8.0-alpha";

            string raw = File.ReadAllText(versionFile).Trim();
            if (raw.StartsWith("smb2-v", StringComparison.OrdinalIgnoreCase))
                raw = raw.Substring("smb2-v".Length);
            else if (raw.StartsWith("v", StringComparison.OrdinalIgnoreCase))
                raw = raw.Substring(1);

            return string.IsNullOrWhiteSpace(raw) ? "0.8.0-alpha" : raw;
        }
    }
}
#endif

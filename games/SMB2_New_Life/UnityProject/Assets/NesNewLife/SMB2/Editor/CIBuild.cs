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
        private const string BuildFolder = "build/StandaloneWindows64";
        private const string ExePath = BuildFolder + "/NES_New_Life_SMB2.exe";
        private const string VersionFile = "VERSION";

        public static void BuildWindows()
        {
            Debug.Log("[NES New Life CI] Preparing SMB2 Windows x64 release build...");
            Directory.CreateDirectory(BuildFolder);

            if (!CampaignScenesExist())
            {
                Debug.Log($"[NES New Life CI] Campaign scenes missing. Generating {CampaignCatalog.StageCount} stages...");
                CreateCampaignScenes.Create();
                AssetDatabase.Refresh();
            }

            if (!CampaignScenesExist())
                throw new Exception("Campaign generation failed: one or more stage scenes are missing.");

            if (!ValidateCampaign.ValidateForBuild())
                throw new Exception("Campaign structural validation failed. CI build aborted.");

            string version = ResolveVersion();
            ConfigurePlayer(version);

            var options = new BuildPlayerOptions
            {
                scenes = CreateCampaignScenes.StagePaths,
                locationPathName = ExePath,
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
            File.WriteAllText(Path.Combine(BuildFolder, "BUILD_INFO.txt"), info);

            Debug.Log("[NES New Life CI] Windows executable created at: " + ExePath);
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

        private static string ResolveVersion()
        {
            if (!File.Exists(VersionFile))
                return "0.8.0-alpha";

            string raw = File.ReadAllText(VersionFile).Trim();
            if (raw.StartsWith("smb2-v", StringComparison.OrdinalIgnoreCase))
                raw = raw.Substring("smb2-v".Length);
            else if (raw.StartsWith("v", StringComparison.OrdinalIgnoreCase))
                raw = raw.Substring(1);

            return string.IsNullOrWhiteSpace(raw) ? "0.8.0-alpha" : raw;
        }
    }
}
#endif

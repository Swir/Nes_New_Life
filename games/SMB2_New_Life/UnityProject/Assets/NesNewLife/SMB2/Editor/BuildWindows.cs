#if UNITY_EDITOR
using System.IO;
using UnityEditor;
using UnityEngine;

namespace NesNewLife.SMB2.EditorTools
{
    public static class BuildWindows
    {
        private const string OutputPath = "Builds/Windows/NES_New_Life_SMB2.exe";

        [MenuItem("NES New Life/SMB2/Build Windows x64")]
        public static void Build()
        {
            bool campaignReady = true;
            foreach (string path in CreateCampaignScenes.StagePaths)
            {
                if (!File.Exists(path))
                {
                    campaignReady = false;
                    break;
                }
            }

            if (!campaignReady)
            {
                Debug.Log($"NES New Life: campaign scenes missing; generating the {CampaignCatalog.StageCount}-stage campaign before build.");
                CreateCampaignScenes.Create();
                AssetDatabase.Refresh();
            }

            foreach (string path in CreateCampaignScenes.StagePaths)
            {
                if (!File.Exists(path))
                {
                    Debug.LogError($"NES New Life: campaign generation failed; missing {path}. Build aborted.");
                    return;
                }
            }

            string outputDirectory = Path.GetDirectoryName(OutputPath);
            if (!string.IsNullOrEmpty(outputDirectory))
                Directory.CreateDirectory(outputDirectory);

            BuildPlayerOptions options = new BuildPlayerOptions
            {
                scenes = CreateCampaignScenes.StagePaths,
                locationPathName = OutputPath,
                target = BuildTarget.StandaloneWindows64,
                options = BuildOptions.None
            };

            var report = BuildPipeline.BuildPlayer(options);
            if (report.summary.result == UnityEditor.Build.Reporting.BuildResult.Succeeded)
            {
                Debug.Log($"NES New Life {CampaignCatalog.StageCount}-stage campaign build ready: {OutputPath} ({report.summary.totalSize} bytes)");
                EditorUtility.RevealInFinder(OutputPath);
            }
            else
            {
                Debug.LogError($"NES New Life build failed: {report.summary.result}");
            }
        }
    }
}
#endif

#if UNITY_EDITOR
using System.IO;
using UnityEditor;
using UnityEngine;

namespace NesNewLife.SMB2.EditorTools
{
    public static class BuildWindows
    {
        private const string ScenePath = "Assets/NesNewLife/SMB2/Prototype/SMB2_Playable.unity";
        private const string OutputPath = "Builds/Windows/NES_New_Life_SMB2.exe";

        [MenuItem("NES New Life/SMB2/Build Windows x64")]
        public static void Build()
        {
            if (!File.Exists(ScenePath))
            {
                Debug.Log("NES New Life: playable scene is missing; generating it before build.");
                CreatePrototypeScene.CreatePlayable();
                AssetDatabase.Refresh();
            }

            if (!File.Exists(ScenePath))
            {
                Debug.LogError("NES New Life: scene generation failed, build aborted.");
                return;
            }

            string outputDirectory = Path.GetDirectoryName(OutputPath);
            if (!string.IsNullOrEmpty(outputDirectory))
                Directory.CreateDirectory(outputDirectory);

            BuildPlayerOptions options = new BuildPlayerOptions
            {
                scenes = new[] { ScenePath },
                locationPathName = OutputPath,
                target = BuildTarget.StandaloneWindows64,
                options = BuildOptions.None
            };

            var report = BuildPipeline.BuildPlayer(options);
            if (report.summary.result == UnityEditor.Build.Reporting.BuildResult.Succeeded)
            {
                Debug.Log($"NES New Life build ready: {OutputPath} ({report.summary.totalSize} bytes)");
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

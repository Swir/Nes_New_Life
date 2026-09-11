#if UNITY_EDITOR
using System.IO;
using UnityEditor;
using UnityEditor.Build;
using UnityEditor.Build.Reporting;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.SceneManagement;

namespace NesNewLife.SMB2.EditorTools
{
    public sealed class PixelArtBuildPreprocessor : IPreprocessBuildWithReport
    {
        public int callbackOrder => 100;

        public void OnPreprocessBuild(BuildReport report)
        {
            UpgradeAllCampaignScenes();
        }

        [MenuItem("NES New Life/SMB2/Upgrade ALL Campaign Visuals")]
        public static void UpgradeAllCampaignScenes()
        {
            int upgraded = 0;

            foreach (string path in CreateCampaignScenes.StagePaths)
            {
                if (!File.Exists(path))
                    continue;

                Scene scene = EditorSceneManager.OpenScene(path, OpenSceneMode.Single);
                PixelArtVisualPass.ApplyCurrentScene();
                EditorSceneManager.MarkSceneDirty(scene);
                EditorSceneManager.SaveScene(scene, path);
                upgraded++;
            }

            AssetDatabase.SaveAssets();
            AssetDatabase.Refresh(ImportAssetOptions.ForceSynchronousImport);
            Debug.Log($"NES New Life: pixel-art visuals applied to {upgraded}/{CreateCampaignScenes.StagePaths.Length} campaign scenes.");
        }
    }
}
#endif

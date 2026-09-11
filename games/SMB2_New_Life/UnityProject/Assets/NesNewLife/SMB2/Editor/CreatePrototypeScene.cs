#if UNITY_EDITOR
using System.IO;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.SceneManagement;

namespace NesNewLife.SMB2.EditorTools
{
    public static class CreatePrototypeScene
    {
        private const string SceneDirectory = "Assets/NesNewLife/SMB2/Prototype";
        private const string ScenePath = SceneDirectory + "/SMB2_Prototype.unity";

        [MenuItem("NES New Life/SMB2/Create Prototype Scene")]
        public static void Create()
        {
            Scene scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);

            Sprite builtinSprite = AssetDatabase.GetBuiltinExtraResource<Sprite>("UI/Skin/UISprite.psd");

            GameObject ground = CreateBlock(
                "Ground",
                new Vector2(0f, -2.5f),
                new Vector2(24f, 1f),
                new Color(0.18f, 0.24f, 0.32f),
                builtinSprite
            );
            ground.AddComponent<BoxCollider2D>();

            CreatePlatform(new Vector2(-6f, -0.5f), new Vector2(4f, 0.5f), builtinSprite);
            CreatePlatform(new Vector2(4.5f, 0.75f), new Vector2(5f, 0.5f), builtinSprite);

            GameObject player = CreatePlayer(builtinSprite);
            CreateCarryable(new Vector2(1.5f, -1.5f), builtinSprite, new Color(0.95f, 0.55f, 0.20f));
            CreateCarryable(new Vector2(5.0f, 1.5f), builtinSprite, new Color(0.90f, 0.25f, 0.28f));

            CreateCamera(player.transform);

            Directory.CreateDirectory(SceneDirectory);
            AssetDatabase.Refresh();
            EditorSceneManager.SaveScene(scene, ScenePath);

            Selection.activeGameObject = player;
            EditorGUIUtility.PingObject(player);

            Debug.Log($"NES New Life: prototype scene created at {ScenePath}. Press Play to test it.");
        }

        private static GameObject CreatePlayer(Sprite sprite)
        {
            GameObject player = CreateBlock(
                "Player",
                new Vector2(-2f, -1.25f),
                new Vector2(0.85f, 1.45f),
                new Color(0.25f, 0.70f, 1.0f),
                sprite
            );

            Rigidbody2D body = player.AddComponent<Rigidbody2D>();
            body.gravityScale = 3f;
            body.freezeRotation = true;
            body.collisionDetectionMode = CollisionDetectionMode2D.Continuous;
            body.interpolation = RigidbodyInterpolation2D.Interpolate;

            player.AddComponent<BoxCollider2D>();

            GameObject groundCheck = new GameObject("GroundCheck");
            groundCheck.transform.SetParent(player.transform);
            groundCheck.transform.localPosition = new Vector3(0f, -0.78f, 0f);

            GameObject pickupPoint = new GameObject("PickupPoint");
            pickupPoint.transform.SetParent(player.transform);
            pickupPoint.transform.localPosition = new Vector3(0.65f, -0.55f, 0f);

            GameObject carryAnchor = new GameObject("CarryAnchor");
            carryAnchor.transform.SetParent(player.transform);
            carryAnchor.transform.localPosition = new Vector3(0.25f, 1.05f, 0f);

            PlayerController2D controller = player.AddComponent<PlayerController2D>();
            SerializedObject controllerSO = new SerializedObject(controller);
            controllerSO.FindProperty("groundCheck").objectReferenceValue = groundCheck.transform;
            controllerSO.FindProperty("groundMask").intValue = ~0;
            controllerSO.ApplyModifiedPropertiesWithoutUndo();

            CarrySystem2D carrySystem = player.AddComponent<CarrySystem2D>();
            SerializedObject carrySO = new SerializedObject(carrySystem);
            carrySO.FindProperty("pickupPoint").objectReferenceValue = pickupPoint.transform;
            carrySO.FindProperty("carryAnchor").objectReferenceValue = carryAnchor.transform;
            carrySO.FindProperty("carryableMask").intValue = ~0;
            carrySO.ApplyModifiedPropertiesWithoutUndo();

            return player;
        }

        private static void CreateCarryable(Vector2 position, Sprite sprite, Color color)
        {
            GameObject obj = CreateBlock(
                "Carryable",
                position,
                new Vector2(0.55f, 0.55f),
                color,
                sprite
            );

            Rigidbody2D body = obj.AddComponent<Rigidbody2D>();
            body.gravityScale = 2.5f;
            body.collisionDetectionMode = CollisionDetectionMode2D.Continuous;
            obj.AddComponent<BoxCollider2D>();
            obj.AddComponent<CarryableObject2D>();
        }

        private static void CreatePlatform(Vector2 position, Vector2 scale, Sprite sprite)
        {
            GameObject platform = CreateBlock(
                "Platform",
                position,
                scale,
                new Color(0.30f, 0.42f, 0.50f),
                sprite
            );
            platform.AddComponent<BoxCollider2D>();
        }

        private static GameObject CreateBlock(
            string name,
            Vector2 position,
            Vector2 scale,
            Color color,
            Sprite sprite)
        {
            GameObject obj = new GameObject(name);
            obj.transform.position = position;
            obj.transform.localScale = new Vector3(scale.x, scale.y, 1f);

            SpriteRenderer renderer = obj.AddComponent<SpriteRenderer>();
            renderer.sprite = sprite;
            renderer.color = color;

            return obj;
        }

        private static void CreateCamera(Transform target)
        {
            GameObject cameraObject = new GameObject("Main Camera");
            cameraObject.tag = "MainCamera";
            cameraObject.transform.position = new Vector3(0f, 0f, -10f);

            Camera camera = cameraObject.AddComponent<Camera>();
            camera.orthographic = true;
            camera.orthographicSize = 5f;
            camera.clearFlags = CameraClearFlags.SolidColor;
            camera.backgroundColor = new Color(0.055f, 0.075f, 0.11f);

            CameraFollow2D follow = cameraObject.AddComponent<CameraFollow2D>();
            follow.Target = target;
        }
    }
}
#endif

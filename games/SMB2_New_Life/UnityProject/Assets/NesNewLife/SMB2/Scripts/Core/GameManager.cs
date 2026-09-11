using UnityEngine;
using UnityEngine.SceneManagement;

namespace NesNewLife.SMB2
{
    public enum RunState
    {
        CharacterSelect,
        Playing,
        Paused,
        Won,
        GameOver
    }

    public sealed class GameManager : MonoBehaviour
    {
        public static GameManager Instance { get; private set; }

        [SerializeField] private int startingLives = 3;
        [SerializeField] private CharacterType selectedCharacter = CharacterType.Mario;

        private Transform player;
        private Vector3 checkpoint;
        private int lives;
        private int score;
        private RunState state;

        public int Lives => lives;
        public int Score => score;
        public RunState State => state;
        public CharacterType SelectedCharacter => selectedCharacter;
        public Vector3 Checkpoint => checkpoint;

        private void Awake()
        {
            if (Instance != null && Instance != this)
            {
                Destroy(gameObject);
                return;
            }

            Instance = this;
            lives = Mathf.Max(1, startingLives);
            state = RunState.CharacterSelect;
            Time.timeScale = 0f;
        }

        private void Start()
        {
            PlayerController2D controller = FindFirstObjectByType<PlayerController2D>();
            if (controller != null)
            {
                player = controller.transform;
                checkpoint = player.position;
                ApplyCharacter(selectedCharacter);
            }
        }

        private void Update()
        {
            if (state == RunState.CharacterSelect)
            {
                if (Input.GetKeyDown(KeyCode.Alpha1)) StartWithCharacter(CharacterType.Mario);
                else if (Input.GetKeyDown(KeyCode.Alpha2)) StartWithCharacter(CharacterType.Luigi);
                else if (Input.GetKeyDown(KeyCode.Alpha3)) StartWithCharacter(CharacterType.Peach);
                else if (Input.GetKeyDown(KeyCode.Alpha4)) StartWithCharacter(CharacterType.Toad);
                return;
            }

            if (state == RunState.Playing && (Input.GetKeyDown(KeyCode.Escape) || Input.GetKeyDown(KeyCode.P)))
            {
                state = RunState.Paused;
                Time.timeScale = 0f;
                return;
            }

            if (state == RunState.Paused && (Input.GetKeyDown(KeyCode.Escape) || Input.GetKeyDown(KeyCode.P)))
            {
                state = RunState.Playing;
                Time.timeScale = 1f;
                return;
            }

            if ((state == RunState.Won || state == RunState.GameOver) && Input.GetKeyDown(KeyCode.R))
                RestartScene();
        }

        public void RegisterPlayer(Transform playerTransform)
        {
            player = playerTransform;
            checkpoint = player.position;
            ApplyCharacter(selectedCharacter);
        }

        public void StartWithCharacter(CharacterType type)
        {
            ApplyCharacter(type);
            state = RunState.Playing;
            Time.timeScale = 1f;
        }

        public void ApplyCharacter(CharacterType type)
        {
            selectedCharacter = type;
            if (player == null)
                return;

            CharacterTuning tuning = CharacterTuning.For(type);
            PlayerController2D controller = player.GetComponent<PlayerController2D>();
            CarrySystem2D carry = player.GetComponent<CarrySystem2D>();
            SpriteRenderer renderer = player.GetComponent<SpriteRenderer>();

            if (controller != null) controller.ApplyTuning(tuning);
            if (carry != null) carry.SetThrowHorizontalSpeed(tuning.ThrowSpeed);
            if (renderer != null) renderer.color = tuning.Color;
        }

        public void AddScore(int amount)
        {
            if (state != RunState.Playing)
                return;
            score = Mathf.Max(0, score + amount);
        }

        public void SetCheckpoint(Vector3 worldPosition)
        {
            checkpoint = worldPosition;
        }

        public void PlayerDied()
        {
            if (state != RunState.Playing)
                return;

            lives--;
            if (lives <= 0)
            {
                state = RunState.GameOver;
                Time.timeScale = 0f;
                return;
            }

            RespawnPlayer();
        }

        public void RespawnPlayer()
        {
            if (player == null)
                return;

            Rigidbody2D body = player.GetComponent<Rigidbody2D>();
            if (body != null)
                body.linearVelocity = Vector2.zero;

            player.position = checkpoint;
            PlayerHealth health = player.GetComponent<PlayerHealth>();
            if (health != null)
                health.RestoreFull();
        }

        public void Win()
        {
            if (state != RunState.Playing)
                return;

            score += 5000;
            state = RunState.Won;
            Time.timeScale = 0f;
        }

        public void RestartScene()
        {
            Time.timeScale = 1f;
            Scene active = SceneManager.GetActiveScene();
            if (active.buildIndex >= 0)
                SceneManager.LoadScene(active.buildIndex);
            else
                SceneManager.LoadScene(active.name);
        }

        private void OnDestroy()
        {
            if (Instance == this)
            {
                Time.timeScale = 1f;
                Instance = null;
            }
        }
    }
}

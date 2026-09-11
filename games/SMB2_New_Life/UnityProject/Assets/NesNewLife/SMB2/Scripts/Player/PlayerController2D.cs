using UnityEngine;

namespace NesNewLife.SMB2
{
    [RequireComponent(typeof(Rigidbody2D))]
    public sealed class PlayerController2D : MonoBehaviour
    {
        [Header("References")]
        [SerializeField] private Transform groundCheck;
        [SerializeField] private LayerMask groundMask;

        [Header("Horizontal Movement")]
        [SerializeField, Min(0.1f)] private float maxMoveSpeed = 6f;
        [SerializeField, Min(0.1f)] private float groundAcceleration = 55f;
        [SerializeField, Min(0.1f)] private float groundDeceleration = 70f;
        [SerializeField, Range(0f, 1f)] private float airControl = 0.65f;

        [Header("Jump")]
        [SerializeField, Min(0.1f)] private float jumpVelocity = 12f;
        [SerializeField, Min(1f)] private float fallingGravityMultiplier = 1.8f;
        [SerializeField, Min(1f)] private float shortJumpGravityMultiplier = 2.6f;
        [SerializeField, Min(0.01f)] private float groundCheckRadius = 0.14f;
        [SerializeField, Min(0f)] private float coyoteTime = 0.08f;
        [SerializeField, Min(0f)] private float jumpBufferTime = 0.10f;

        [Header("Crouch / Charge Jump")]
        [SerializeField] private KeyCode crouchKey = KeyCode.DownArrow;
        [SerializeField] private KeyCode crouchAlternateKey = KeyCode.S;
        [SerializeField, Min(0.1f)] private float maxCrouchChargeTime = 1f;
        [SerializeField, Min(0f)] private float maxCrouchJumpBonus = 3f;

        [Header("Float")]
        [SerializeField, Min(0f)] private float floatSeconds;
        [SerializeField, Min(0.1f)] private float floatFallSpeed = 2.0f;

        [Header("Climbing")]
        [SerializeField, Min(0.1f)] private float climbSpeed = 4.2f;
        [SerializeField, Range(0.1f, 1f)] private float climbHorizontalControl = 0.45f;

        private Rigidbody2D body;
        private float horizontalInput;
        private float verticalInput;
        private float coyoteCounter;
        private float jumpBufferCounter;
        private float crouchCharge;
        private float floatRemaining;
        private float defaultGravityScale;
        private bool jumpHeld;
        private bool isGrounded;
        private bool isCrouching;
        private bool touchingClimbable;
        private bool isClimbing;
        private int facingSign = 1;

        public bool IsGrounded => isGrounded;
        public bool IsCrouching => isCrouching;
        public bool IsClimbing => isClimbing;
        public int FacingSign => facingSign;
        public Vector2 Velocity => body != null ? body.linearVelocity : Vector2.zero;

        private void Awake()
        {
            body = GetComponent<Rigidbody2D>();
            defaultGravityScale = body.gravityScale;
        }

        private void Update()
        {
            if (GameManager.Instance != null && GameManager.Instance.State != RunState.Playing)
                return;

            ReadInput();
            UpdateGroundState();
            UpdateClimbingState();
            UpdateJumpTimers();
            UpdateCrouchCharge();
            TryConsumeJump();
        }

        private void FixedUpdate()
        {
            if (GameManager.Instance != null && GameManager.Instance.State != RunState.Playing)
            {
                body.linearVelocity = Vector2.zero;
                return;
            }

            if (isClimbing)
            {
                ApplyClimbingMovement();
                return;
            }

            ApplyHorizontalMovement();
            ApplyBetterJumpGravity();
        }

        public void ApplyTuning(CharacterTuning tuning)
        {
            maxMoveSpeed = tuning.MoveSpeed;
            groundAcceleration = tuning.Acceleration;
            jumpVelocity = tuning.JumpVelocity;
            airControl = tuning.AirControl;
            floatSeconds = tuning.FloatSeconds;
            floatRemaining = floatSeconds;
        }

        public void SetClimbableContact(bool touching)
        {
            touchingClimbable = touching;
            if (!touching)
                StopClimbing();
        }

        private void ReadInput()
        {
            bool left = Input.GetKey(KeyCode.A) || Input.GetKey(KeyCode.LeftArrow);
            bool right = Input.GetKey(KeyCode.D) || Input.GetKey(KeyCode.RightArrow);
            bool up = Input.GetKey(KeyCode.W) || Input.GetKey(KeyCode.UpArrow);
            bool down = Input.GetKey(KeyCode.S) || Input.GetKey(KeyCode.DownArrow);

            horizontalInput = (right ? 1f : 0f) - (left ? 1f : 0f);
            verticalInput = (up ? 1f : 0f) - (down ? 1f : 0f);

            jumpHeld = Input.GetKey(KeyCode.Space);
            if (Input.GetKeyDown(KeyCode.Space))
                jumpBufferCounter = jumpBufferTime;

            isCrouching = !isClimbing && (Input.GetKey(crouchKey) || Input.GetKey(crouchAlternateKey));

            if (Mathf.Abs(horizontalInput) > 0.01f)
                facingSign = horizontalInput > 0f ? 1 : -1;
        }

        private void UpdateGroundState()
        {
            if (groundCheck == null)
            {
                isGrounded = false;
                return;
            }

            isGrounded = Physics2D.OverlapCircle(groundCheck.position, groundCheckRadius, groundMask) != null;
            if (isGrounded)
                floatRemaining = floatSeconds;
        }

        private void UpdateClimbingState()
        {
            if (!touchingClimbable)
                return;

            if (!isClimbing && Mathf.Abs(verticalInput) > 0.01f)
            {
                isClimbing = true;
                body.gravityScale = 0f;
                body.linearVelocity = Vector2.zero;
            }

            if (isClimbing && Input.GetKeyDown(KeyCode.Space))
            {
                StopClimbing();
                body.linearVelocity = new Vector2(body.linearVelocity.x, jumpVelocity * 0.85f);
                jumpBufferCounter = 0f;
            }
        }

        private void StopClimbing()
        {
            if (!isClimbing)
                return;

            isClimbing = false;
            if (body != null)
                body.gravityScale = defaultGravityScale;
        }

        private void UpdateJumpTimers()
        {
            coyoteCounter = isGrounded ? coyoteTime : Mathf.Max(0f, coyoteCounter - Time.deltaTime);
            jumpBufferCounter = Mathf.Max(0f, jumpBufferCounter - Time.deltaTime);
        }

        private void UpdateCrouchCharge()
        {
            if (isGrounded && isCrouching)
            {
                crouchCharge = Mathf.Min(maxCrouchChargeTime, crouchCharge + Time.deltaTime);
                return;
            }

            if (isGrounded && !isCrouching && jumpBufferCounter <= 0f)
                crouchCharge = Mathf.MoveTowards(crouchCharge, 0f, Time.deltaTime * 2f);
        }

        private void TryConsumeJump()
        {
            if (isClimbing || jumpBufferCounter <= 0f || coyoteCounter <= 0f)
                return;

            float charge01 = maxCrouchChargeTime <= 0f ? 0f : Mathf.Clamp01(crouchCharge / maxCrouchChargeTime);
            float finalJumpVelocity = jumpVelocity + (maxCrouchJumpBonus * charge01);

            Vector2 velocity = body.linearVelocity;
            velocity.y = finalJumpVelocity;
            body.linearVelocity = velocity;

            jumpBufferCounter = 0f;
            coyoteCounter = 0f;
            crouchCharge = 0f;
            floatRemaining = floatSeconds;
        }

        private void ApplyClimbingMovement()
        {
            body.gravityScale = 0f;
            body.linearVelocity = new Vector2(
                horizontalInput * maxMoveSpeed * climbHorizontalControl,
                verticalInput * climbSpeed
            );
        }

        private void ApplyHorizontalMovement()
        {
            float targetSpeed = isCrouching && isGrounded ? 0f : horizontalInput * maxMoveSpeed;
            float acceleration = Mathf.Abs(targetSpeed) > 0.01f ? groundAcceleration : groundDeceleration;
            if (!isGrounded)
                acceleration *= airControl;

            float newX = Mathf.MoveTowards(body.linearVelocity.x, targetSpeed, acceleration * Time.fixedDeltaTime);
            body.linearVelocity = new Vector2(newX, body.linearVelocity.y);
        }

        private void ApplyBetterJumpGravity()
        {
            bool canFloat = floatRemaining > 0f && jumpHeld && body.linearVelocity.y <= 0.5f && !isGrounded;
            if (canFloat)
            {
                floatRemaining = Mathf.Max(0f, floatRemaining - Time.fixedDeltaTime);
                body.linearVelocity = new Vector2(body.linearVelocity.x, Mathf.Max(body.linearVelocity.y, -floatFallSpeed));
                body.linearVelocity += Physics2D.gravity * (0.18f * Time.fixedDeltaTime);
                return;
            }

            if (body.linearVelocity.y < -0.01f)
            {
                body.linearVelocity += Physics2D.gravity * ((fallingGravityMultiplier - 1f) * Time.fixedDeltaTime);
            }
            else if (body.linearVelocity.y > 0.01f && !jumpHeld)
            {
                body.linearVelocity += Physics2D.gravity * ((shortJumpGravityMultiplier - 1f) * Time.fixedDeltaTime);
            }
        }

        private void OnDisable()
        {
            StopClimbing();
        }

        private void OnDrawGizmosSelected()
        {
            if (groundCheck != null)
                Gizmos.DrawWireSphere(groundCheck.position, groundCheckRadius);
        }
    }
}

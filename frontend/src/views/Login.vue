<template>
  <div class="body">
    <div v-if="!loading">
      <div v-if="alert.show" :class="[
        'alert',
        `alert-${alert.color}`,
        'alert-dismissible',
        'fade',
        'show',
        'p-2'
      ]" role="alert">
        <strong>{{ alert.type }}</strong> {{ alert.message }}
        <button type="button" class="btn-close" @click="closeAlert" aria-label="Close"></button>
      </div>

      <div class="container" :class="toggleClass" id="container">
        <!-- Sign Up Form -->
        <div class="form-container sign-up">
          <form @submit.prevent="signUp" novalidate>
            <h1>Create Account</h1>

            <!-- Side-by-side First and Last Name -->
            <div class="name-row">
              <input v-model="signup.F_usr" placeholder="Enter Firstname" required />
              <input v-model="signup.L_usr" placeholder="Enter Lastname" required />
            </div>

            <input v-model="signup.email" type="email" placeholder="Enter Email" required />
            <input v-model="signup.psw" type="password" placeholder="Enter Password" required />
            <input v-model="signup.rpsw" type="password" placeholder="Re-Enter Password" required />
            <button type="submit">Sign Up</button>
          </form>
        </div>

        <!-- Sign In Form -->
        <div class="form-container sign-in">
          <form @submit.prevent="signIn">
            <h1>Sign In</h1>
            <input v-model="signin.email" type="email" name="email" placeholder="Enter Email" required />
            <input v-model="signin.psw" type="password" name="password" placeholder="Enter Password" required />
            <button type="submit">Sign In</button>
          </form>
        </div>

        <!-- Toggle UI -->
        <div class="toggle-container">
          <div class="toggle">
            <div class="toggle-panel toggle-left">
              <h1>Welcome Back!</h1>
              <p>Enter your Personal details to use all of site features</p>
              <button class="hidden" @click="toggleForm">Sign In</button>
            </div>
            <div class="toggle-panel toggle-right">
              <h1>Hello, Friend!</h1>
              <p>
                Register with your Personal details to use all of site features
              </p>
              <button class="hidden" @click="toggleForm">Sign Up</button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div v-else>
      <p>Loading...</p>
    </div>
  </div>
</template>

<script>
export default {
  name: "LoginView",

  data() {
    return {
      loading: false,
      alert: {
        color: "",
        message: "",
        show: false,
        type: "",
      },
      toggle: "",

      // Forms
      signin: {
        email: "",
        psw: "",
      },
      signup: {
        F_usr: "",
        L_usr: "",
        email: "",
        psw: "",
        rpsw: "",
      },

      token: localStorage.getItem("token") || "",
    };
  },

  computed: {
    toggleClass() {
      return this.toggle === "active" ? "active" : "";
    },
  },
  mounted() {
    if (this.token) {
      this.$router.push("/");
      const newId = Date.now()
      this.$emit("show-toast",{ id: newId, message: "Already logged in", color: "bg-success" })
    }
  },
  methods: {
    toggleForm() {
      this.toggle = this.toggle === "active" ? "" : "active";
    },

    closeAlert() {
      this.alert = {
        color: "",
        message: "",
        show: false,
        type: "",
      };
    },

    async signIn() {
      const { email, psw } = this.signin;

      if (!email || !psw) {
        this.alert = {
          color: "danger",
          message: "Username and password are required",
          show: true,
          type: "Error!!",
        };
        return;
      }

      this.loading = true;

      try {
        const response = await fetch("http://127.0.0.1:8000/signin", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email: email, password: psw }),
        });
        const data = await response.json();
        if (response.ok) {
          this.alert = {
            color: "success",
            message: "User logged in successfully",
            show: true,
            type: "Success!!",
          };
          this.token = data.token;
          localStorage.setItem("token", this.token);
          this.$emit("logged-in",{ id: Date.now(), message: "User logged in successfully", color: "bg-success" })
          this.$router.push("/");
        } else {
          this.alert = {
            color: "danger",
            message: data.message || "Error logging in",
            show: true,
            type: "Error!!",
          };
        }
      } catch (error) {
        this.alert = {
          color: "danger",
          message: "Error logging in",
          show: true,
          type: "Error!!",
        };
      } finally {
        this.loading = false;
      }
    },

    async signUp() {
      const { F_usr, L_usr, email, psw, rpsw } = this.signup;

      if (!F_usr || !L_usr || !email || !psw || !rpsw) {
        this.alert = {
          color: "danger",
          message: "All fields are required",
          show: true,
          type: "Error!!",
        };
        return;
      }

      if (psw !== rpsw) {
        this.alert = {
          color: "danger",
          message: "Passwords do not match",
          show: true,
          type: "Error!!",
        };
        return;
      }

      this.loading = true;

      try {
        const response = await fetch("http://127.0.0.1:8000/signup", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            first_name: F_usr,
            last_name: L_usr,
            email: email,
            password: psw,
          }),
        });

        const data = await response.json();

        if (response.ok) {
          this.alert = {
            color: "success",
            message: "Account created successfully!",
            show: true,
            type: "Success!!",
          };
          this.toggleForm(); // Switch to login view
        } else {
          this.alert = {
            color: "danger",
            message: data.message || "Error creating account",
            show: true,
            type: "Error!!",
          };
        }
      } catch (error) {
        this.alert = {
          color: "danger",
          message: "Error creating account",
          show: true,
          type: "Error!!",
        };
      } finally {
        this.loading = false;
      }
    },
  },
};
</script>

<style scoped>
@import url("https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;500;600;700&display=swap");

::-webkit-scrollbar {
  width: 0px;
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
  font-family: "Montserrat", sans-serif;
}

.body {
  background-color: #0d6efd;
  background: linear-gradient(to right, rgb(212, 210, 255), #0d6efd);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-direction: column;
  height: 90vh;
}

.container {
  background-color: #fff;
  border-radius: 30px;
  box-shadow: 0 5px 15px rgba(0, 0, 0, 0.35);
  position: relative;
  overflow: hidden;
  width: 768px;
  max-width: 100%;
  min-height: 480px;
}

.container p {
  font-size: 14px;
  line-height: 20px;
  letter-spacing: 0.3px;
  margin: 20px 0;
}

.container span {
  font-size: 12px;
}

.container a {
  color: #333;
  font-size: 13px;
  text-decoration: none;
  margin: 15px 0 10px;
}

.container button {
  background-color: #0d6efd;
  color: #fff;
  font-size: 12px;
  padding: 10px 45px;
  border: 1px solid transparent;
  border-radius: 8px;
  font-weight: 600;
  letter-spacing: 0.5px;
  text-transform: uppercase;
  margin-top: 10px;
  cursor: pointer;
}

.container button.hidden {
  background-color: transparent;
  border-color: #fff;
}

.container form {
  background-color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-direction: column;
  padding: 0 40px;
  height: 100%;
}

.container input {
  background-color: #eee;
  border: none;
  margin: 8px 0;
  padding: 10px 15px;
  font-size: 13px;
  border-radius: 8px;
  width: 100%;
  outline: none;
}

.name-row {
  display: flex;
  gap: 10px;
}

.name-row input {
  flex: 1;
}


.form-container {
  position: absolute;
  top: 0;
  height: 100%;
  transition: all 0.6s ease-in-out;
}

.sign-in {
  left: 0;
  width: 50%;
  z-index: 2;
}

.container.active .sign-in {
  transform: translateX(100%);
}

.sign-up {
  left: 0;
  width: 50%;
  opacity: 0;
  z-index: 1;
}

.container.active .sign-up {
  transform: translateX(100%);
  opacity: 1;
  z-index: 5;
  animation: move 0.6s;
}

@keyframes move {

  0%,
  49.99% {
    opacity: 0;
    z-index: 1;
  }

  50%,
  100% {
    opacity: 1;
    z-index: 5;
  }
}

.toggle-container {
  position: absolute;
  top: 0;
  left: 50%;
  width: 50%;
  height: 100%;
  overflow: hidden;
  transition: all 0.6s ease-in-out;
  border-radius: 150px 0 0 100px;
  z-index: 1000;
}

.container.active .toggle-container {
  transform: translateX(-100%);
  border-radius: 0 150px 100px 0;
}

.toggle {
  background-color: #0d6efd;
  height: 100%;
  background: linear-gradient(to right,  rgb(212, 210, 255), #0d6efd);
  color: #fff;
  position: relative;
  left: -100%;
  height: 100%;
  width: 200%;
  transform: translateX(0);
  transition: all 0.6s ease-in-out;
}

.container.active .toggle {
  transform: translateX(50%);
}

.toggle-panel {
  position: absolute;
  width: 50%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-direction: column;
  padding: 0 30px;
  text-align: center;
  top: 0;
  transform: translateX(0);
  transition: all 0.6s ease-in-out;
}

.toggle-left {
  transform: translateX(-200%);
}

.container.active .toggle-left {
  transform: translateX(0);
}

.toggle-right {
  right: 0;
  transform: translateX(0);
}

.container.active .toggle-right {
  transform: translateX(200%);
}
</style>

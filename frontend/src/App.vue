<template>
  <nav class="navbar navbar-expand-lg navbar-dark bg-dark h-10">
    <router-link class="navbar-brand mx-1 px-1" to="/">Gods Eye</router-link>
    <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav"
      aria-controls="navbarNav" aria-expanded="false" aria-label="Toggle navigation">
      <span class="navbar-toggler-icon"></span>
    </button>
    <div class="collapse navbar-collapse mx-1 px-1" id="navbarNav">
      <ul class="navbar-nav ms-auto">
        <li class="nav-item">
          <router-link class="nav-link" to="/register" v-show="this.token !== null">Register</router-link>
        </li>
        <li class="nav-item" v-show="this.token !== null">
          <router-link class="nav-link" to="/search">Search</router-link>
        </li>
        <li class="nav-item" v-show="this.token === null">
          <router-link class="nav-link" to="/login">Login</router-link>
        </li>
        <li class="nav-item" v-show="this.token !== null">
          <router-link class="nav-link" @click="logout()" to="/">Logout</router-link>
        </li>
      </ul>
    </div>
  </nav>

  <div aria-live="polite" aria-atomic="true" class="position-relative">
    <div class="toast-container position-absolute top-0 end-0 p-3">
      <transition-group name="toast-slide" tag="div" class="toast-list">
        <div v-for="(toast) in toasts" :key="toast.id" class="toast align-items-center text-white border-0 show mb-2"
          :class="toast.color" role="alert" aria-live="assertive" aria-atomic="true">
          <div class="d-flex">
            <div class="toast-body">
              {{ toast.message }}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" @click="removeToast(toast.id)"
              aria-label="Close"></button>
          </div>
        </div>
      </transition-group>
    </div>
  </div>

  <div class="h-90">
    <router-view @unathorized="clossingUser" @logged-in="logged" @show-toast="addToast" />
  </div>
</template>

<script>
import { reactive } from 'vue'

export default {
  name: 'HomeView',
  data() {
    return {
      toasts: reactive([]),
      token:localStorage.getItem("token")
    }
  },
  mounted() {
    // setInterval(() => {
    // const newId = Date.now()
    //   this.addToast({ id: newId, message: "Already logged in", color: "bg-success" });
    // }, 1000);
  },
  methods: {
    removeToast(id) {
      this.toasts = this.toasts.filter(t => t.id !== id);  // Use `this.toasts` here to access the array
    },
    addToast(data) {
      const newId = Date.now()
      this.toasts.push(data);
      // Auto-remove after 3 seconds
      setTimeout(() => this.removeToast(newId), 2000);
    },
    logout(){
      localStorage.removeItem("token");
      this.token=null
      this.addToast({ id: Date.now(), message: "Logged out successfully", color: "bg-success" });
    },
    logged(data){
      this.addToast(data);
      this.token=localStorage.getItem("token");
    },
    clossingUser(data){
      localStorage.removeItem("token");
      this.token=null;
      this.addToast(data);
    }
  }
}
</script>


<style>
html,
body {
  margin: 0;
  padding: 0;
  background-repeat: repeat;
}

.h-10 {
  height: 10vh;
}

.h-90 {
  height: 90vh;
}

.toast-slide-enter-active,
.toast-slide-leave-active {
  transition: all 0.5s ease;
}

.toast-slide-enter-from {
  transform: translateX(120%);
  opacity: 0;
}

.toast-slide-enter-to {
  transform: translateX(0);
  opacity: 1;
}

.toast-slide-leave-from {
  transform: translateX(0);
  opacity: 1;
}

.toast-slide-leave-to {
  transform: translateX(120%);
  opacity: 0;
}

/* Optional but helps with layout stability */
.toast-list>div {
  display: block;
}

</style>
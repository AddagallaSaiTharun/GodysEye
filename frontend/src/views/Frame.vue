<template>
  <div class="d-flex w-100" style="height: 100%; overflow: hidden">
    <!-- Left Sidebar -->
    <div class="col-2 border-end sidebar-scroll">
      <input type="text" class="w-100 text-center" placeholder="Search" v-model="searchText" />
      <div v-for="(name, index) in filteredNames" :key="index">
        <button class="person-button w-100 text-center" :class="{ clicked: clickedIndex === index }"
          @click="setClickedButton(index, name.id)">
          {{ name.name }}
        </button>
      </div>
    </div>

    <!-- Center Image Display -->
    <div class="d-flex justify-content-center align-items-center"
      :class="{ 'col-6': clickedIndex !== null, 'col-10': clickedIndex === null }">
      <img :src="photoUrl" alt="Frame" style="max-height: 100%; max-width: 100%" v-if="clickedIndex !== null" />
      <div style="max-height: 100%; max-width: 100%" class="d-flex justify-content-center align-items-center"
        v-if="clickedIndex === null">
        Please select a person from the list on the left to view their details.
      </div>
    </div>

    <!-- Right Controls Panel -->
    <!-- col-0 if clickedIndex !== null, col-4 if clickedIndex === null -->
    <div class="col-4 border-start d-flex justify-content-center align-items-center"
      :class="{ 'col-0': clickedIndex === null, 'col-4': clickedIndex !== null }">
      <div class="w-100 px-3">
        <div class="mb-3">
          <label class="form-label">Registered Photo:</label>
          <img :src="registeredPhoto" alt="Frame" style="max-height: 100%; max-width: 100%" />
        </div>
        <div class="mb-3">
          <label class="form-label">From Date:</label>
          <input type="date" v-model="fromDate" class="form-control" />
        </div>
        <div class="mb-3">
          <label class="form-label">To Date:</label>
          <input type="date" v-model="toDate" class="form-control" />
        </div>
        <div class="mb-3">
          <label class="form-label">From Timestamp:</label>
          <input type="time" v-model="fromTime" class="form-control" />
        </div>
        <div class="mb-3">
          <label class="form-label">To Timestamp:</label>
          <input type="time" v-model="toTime" class="form-control" />
        </div>
        <div class="mb-3">
          <label class="form-label">Camera No:</label>
          <select v-model="selectedCamera" class="form-control">
            <option v-for="cam in cameras" :key="cam" :value="cam">
              {{ cam }}
            </option>
          </select>
        </div>
        <div class="d-flex align-items-center gap-2">
          <button @click="prevFrame" class="btn btn-outline-primary">
            Previous Frame
          </button>

          <div class="d-flex align-items-center">
            <input type="number" v-model="frame_id" class="form-control text-center" style="width: 80px;">
            <span class="mx-2">/ {{ total_frames }}</span>
          </div>

          <button @click="nextFrame" class="btn btn-outline-primary">
            Next Frame
          </button>
        </div>


      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: "FrameView",
  data() {
    return {
      names: [],
      photoUrl: "images/placeholder.jpg",
      fromDate: "",
      toDate: "",
      fromTime: "",
      toTime: "",
      selectedCamera: "",
      cameras: [],
      clickedIndex: null,
      searchText: "",
      token: localStorage.getItem("token"),
      registeredPhoto: "",
      frame_id: 1,
      total_frames: 0
    };
  },
  computed: {
    filteredNames() {
      return this.names.filter(
        (name) =>
          name["first_name"]
            .toLowerCase()
            .includes(this.searchText.toLowerCase()) ||
          name["last_name"].toLowerCase().includes(this.searchText.toLowerCase())
      );
    },
  },
  async mounted() {
    let data = await this.get_names();
    this.names = data['persons'];
  },
  beforeMount() {
    if (!this.token) {
      this.$router.push("/login");
      localStorage.removeItem("token")
      const newId = Date.now();
      this.$emit("unathorized", { id: newId, message: "Unauthorized Access! Please Login", color: "bg-danger" });
      return;
    }
  },
  methods: {
    async nextFrame() {
      this.frame_id += 1;
      if (this.frame_id >= this.total_frames) {
        this.frame_id = this.total_frames;
        console.log("last");
        return;
      }
      let data = await this.get_person_details(this.names[this.clickedIndex]['id']);
      this.cameras = data['data']['camera_names'];
      this.photoUrl = data['data']['frame_image'];
      this.registeredPhoto = data['data']['registered_photo'];
      this.selectedCamera = data['data']['present_camera'];
    },
    async prevFrame() {
      this.frame_id -= 1;
      if (this.frame_id <= 0) {
        console.log("first");
        this.frame_id = 0;
        return;
      }
      let data = await this.get_person_details(this.names[this.clickedIndex]['id']);
      this.cameras = data['data']['camera_names'];
      this.photoUrl = data['data']['frame_image'];
      this.registeredPhoto = data['data']['registered_photo'];
      this.selectedCamera = data['data']['present_camera'];

    },
    async setClickedButton(index, id) {
      this.clickedIndex = index;
      let data = await this.get_person_details(id);
      console.log(data);
      this.frame_id = 1;
      this.cameras = data['data']['camera_names'];
      this.photoUrl = data['data']['frame_image'];
      this.registeredPhoto = data['data']['registered_photo'];
      this.selectedCamera = data['data']['present_camera'];
      this.total_frames = data['data']['total_frames']
    },
    async get_names() {
      // const query = new URLSearchParams({
      //   camera_id: "0",
      //   frame_id: "frame_0",
      // });

      try {
        const response = await fetch(`/api/missing_person_frame`, {
          method: "GET",
          headers: {
            "Content-Type": "application/json",
            "authorization": `Bearer ${this.token}`,
          },
        });
        if (response.status === 401) {
          // Handle unauthorized: remove token & redirect
          localStorage.removeItem("token");
          this.$router.push("/login");
          const newId = Date.now();
          this.$emit("unathorized", { id: newId, message: "Unauthorized Access! Please Login", color: "bg-danger" });
          return;
        }
        let data = await response.json();
        return data;
      } catch (e) {
        console.error("Error fetching names:", e);
      }
    },

    async get_person_details(id) {
      const query = new URLSearchParams({
        missing_person_id: id,
      });
      try {
        const response = await fetch(`/api/missing_person_frame?${query}`, {
          method: "GET",
          headers: {
            "Content-Type": "application/json",
            "authorization": `Bearer ${this.token}`,
          },
        });

        if (response.status === 401) {
          // Remove token and redirect to login
          localStorage.removeItem("token");
          this.$router.push("/login");
          const newId = Date.now();
          this.$emit("unathorized", { id: newId, message: "Unauthorized Access! Please Login", color: "bg-danger" });
          return;
        }

        return await response.json();
      } catch (e) {
        console.error("Failed to fetch person details", e);
      }
    },
  },
};
</script>

<style scoped>
.sidebar-scroll {
  height: 100vh;
  overflow-y: auto;
  scrollbar-width: 1px;
  /* Firefox */
}

.sidebar-scroll::-webkit-scrollbar {
  width: 1px;
  /* Chrome, Safari */
}

.sidebar-scroll::-webkit-scrollbar-thumb {
  background-color: #6c757d;
  border-radius: 10px;
}

.person-button {
  background-color: #f8f9fa;
  border: 1px solid #ced4da;
  padding: 0.5rem 1rem;
  font-size: 0.95rem;
  transition: background-color 0.3s ease, transform 0.2s ease;
}

.person-button:hover,
.person-button.clicked {
  background-color: #e2e6ea;
  transform: scale(1.02);
  cursor: pointer;
}

.person-button:focus {
  outline: none;
  box-shadow: 0 0 0 2px #0d6efd50;
}
</style>

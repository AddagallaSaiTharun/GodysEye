<template>
  <div class="body">

    <div class="form-container my-5">
      <h2>Report Missing Person</h2>
      <form @submit.prevent="submitForm" novalidate>
        <div class="form-group">
          <label for="name">First Name *</label>
          <input type="text" v-model="form.first_name" required />
          <span v-if="formErrors.first_name" class="error">Name is required.</span>
        </div>

        <div class="form-group">
          <label for="name">Last Name *</label>
          <input type="text" v-model="form.last_name" required />
          <span v-if="formErrors.last_name" class="error">Name is required.</span>
        </div>

        <div class="form-group">
          <label for="details">Details *</label>
          <textarea v-model="form.details" required rows="4"></textarea>
          <span v-if="formErrors.details" class="error">Details are required.</span>
        </div>

        <div class="form-group">
          <label for="photo">Person Photo *</label>
          <input type="file" @change="handleFileChange('photo', $event)" accept="image/*" required />
          <span v-if="formErrors.photo" class="error">Please upload a valid image file.</span>
          <img v-if="photoPreview" :src="photoPreview" alt="Photo Preview" style="display: block; max-width: 100%;max-height: 30vh; margin-top: 10px;" />
        </div>

        <div class="form-group">
          <label for="video">Person Video (Optional)</label>
          <input type="file" @change="handleFileChange('video', $event)" accept="video/*" />
          <span v-if="formErrors.video" class="error">Please upload a valid video file.</span>
          <video v-if="videoPreview" :src="videoPreview" controls style="max-width: 100%;max-height: 30vh; margin-top: 10px;"/>
        </div>

        <button type="submit" :disabled="load">Submit Report</button>
      </form>
    </div>

  </div>
</template>

<script>
export default {
  data() {
    return {
      form: {
        first_name: '',
        last_name: '',
        details: '',
        photo: null,
        video: null,
      },
      formErrors: {
        first_name: false,
        last_name: false,
        details: false,
        photo: false,
        video: false,
      },
      photoPreview: null,
      videoPreview: null,
      load:false,
      token: localStorage.getItem("token")
    };
  },
  beforeMount() {
    if (!this.token) {
      this.$router.push("/login");
      const newId = Date.now();
      this.$emit("show-toast", { id: newId, message: "Unauthorized Access! Please Login", color: "bg-danger" });
    }
  },
  methods: {
    handleFileChange(type, event) {
      const file = event.target.files[0];
      if (type === 'photo') {
        if (file && file.type.startsWith('image/')) {
          const reader = new FileReader();
          reader.onload = () => {
            this.photoPreview = reader.result;
          };
          reader.readAsDataURL(file);
          this.form.photo = file;
        } else {
          this.photoPreview = null;
        }
      } else if (type === 'video') {
        if (file && file.type.startsWith('video/')) {
          const reader = new FileReader();
          reader.onload = () => {
            this.videoPreview = reader.result;
          };
          reader.readAsDataURL(file);
          this.form.video = file;
        } else {
          this.videoPreview = null;
        }
      }
    },
    async submitForm() {
      this.load=true;
      this.formErrors.first_name = !this.form.first_name.trim();
      this.formErrors.last_name = !this.form.last_name.trim();
      this.formErrors.details = !this.form.details.trim();
      this.formErrors.photo = !this.form.photo || !this.form.photo.type.startsWith('image/');
      this.formErrors.video = this.form.video && !this.form.video.type.startsWith('video/');

      if (Object.values(this.formErrors).includes(true)) {
        return;
      }

      const formData = new FormData();
      formData.append("first_name", this.form.first_name);
      formData.append("last_name", this.form.last_name);
      formData.append("details", this.form.details);
      formData.append("photo", this.form.photo);
      if (this.form.video) {
        formData.append("video", this.form.video);
      }

      try {
        this.load=true;
        const response = await fetch("http://127.0.0.1:8000/missing_persons", {
          method: "POST",
          headers: {
            "Authorization": `Bearer ${this.token}`
          },
          body: formData
        });

        const newId = Date.now();
        if (response.ok) {
          this.$emit("show-toast", { id: newId, message: "Data sent successfully", color: "bg-success" });
          this.resetForm();
        } else if(response.status === 401){
          localStorage.removeItem("token");
          this.$emit("show-toast", { id: newId, message: "Unauthorized Access! Please Login", color: "bg-danger" });
          this.$router.push("/login");
        } else {
          this.$emit("show-toast", { id: newId, message: "Something went wrong. Please try again.", color: "bg-warning" });
        }
      } catch (error) {
        let newId = Date.now();
        console.error("Error submitting form:", error);
        this.$emit("show-toast", { id: newId, message: "Something went wrong. Please try again.", color: "bg-danger" });
      }finally{
        this.load=false;
      }
    },
    resetForm() {
      this.form = {
        last_name: '',
        first_name: '',
        details: '',
        photo: null,
        video: null,
      };
      this.formErrors = {
        last_name: false,
        first_name: false,
        details: false,
        photo: false,
        video: false,
      };
      this.photoPreview = null;
      this.videoPreview = null;
    }
  }
};
</script>

<style scoped>
.body {
  font-family: Arial, sans-serif;
  background: #f2f2f2;
  display: flex;
  justify-content: center;
  align-items: center;
  margin: 0;
}

.form-container {
  background: #fff;
  padding: 30px;
  border-radius: 10px;
  box-shadow: 0 0 20px rgba(0, 0, 0, 0.1);
  width: 100%;
  max-width: 700px;
}

.form-container h2 {
  text-align: center;
  margin-bottom: 20px;
}

.form-group {
  margin-bottom: 15px;
}

label {
  display: block;
  margin-bottom: 5px;
  font-weight: bold;
}

input,
textarea {
  width: 100%;
  padding: 10px;
  border: 1px solid #ccc;
  border-radius: 5px;
  font-size: 14px;
}

input[type="file"] {
  padding: 5px;
}

#photo-preview {
  margin-top: 10px;
  max-width: 100%;
  border: 1px solid #ddd;
  padding: 5px;
  border-radius: 5px;
}

button {
  width: 100%;
  background: #007bff;
  color: white;
  padding: 12px;
  border: none;
  border-radius: 5px;
  font-size: 16px;
  cursor: pointer;
}

button:hover {
  background: #0056b3;
}

.error {
  color: red;
  font-size: 13px;
  display: none;
}
</style>
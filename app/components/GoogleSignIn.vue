<template>
  <div class="gbtn">
    <!-- The container where the Google Sign-In button will be rendered -->
    <div id="g_id_signin"></div>
  </div>
</template>

<script>
export default {
  methods: {
    onGoogleSignIn(response) {
      const idToken = response.credential;
      this.$store.commit('setAuthenticated', true);
      this.$router.push('/orders');

      // Send the ID token to the backend for verification
      this.$axios
        .post("/google-auth", { id_token: idToken })
        .then((res) => {
          console.log("User signed in:", res.data);
          // Handle the sign-in success (e.g., save token and redirect)
        })
        .catch((err) => {
          console.error("Sign-in error:", err);
        });
    },
  },
  mounted() {
    // Ensure the window is loaded with the Google Sign-In script
    window.onGoogleSignIn = this.onGoogleSignIn;

    // Render the Google Sign-In button
    google.accounts.id.initialize({
      client_id: process.env.GOOGLE_CLIENT_ID,
      callback: this.onGoogleSignIn,
    });

    google.accounts.id.renderButton(
      document.getElementById("g_id_signin"),
      { theme: "outline", size: "large" } // Customize the button appearance
    );

    // Optional: to prompt a one-tap sign-in automatically (if you want)
    google.accounts.id.prompt();
  },
};
</script>

<style scoped>
.gbtn{
    padding-top: 25px;
}
.gbtn button {
  border: none;
}
</style>

<template>
  <v-data-table
    :headers="headers"
    :items="users"
  >
    <template v-slot:[`item.edit`]="{ item }">
      <v-btn color="primary" @click="editItem(item)"> Edit </v-btn>
    </template> 
    <template v-slot:[`item.delete`]="{ item }">
      <v-btn color="primary" @click="deleteItem(item)"> Delete </v-btn>
    </template>
    
  </v-data-table>
</template>

<script>
  export default {
    data () {
      return {
        headers: [
          { text: 'Email', value: 'email' },
          { text: 'Edit', value: 'edit' },
          { text: 'Delete', value: 'delete' },
        ],
        
      };
    },
    computed: {
      users(){
        return this.$store.state.users.data
      }

    },

    async fetch(){
      await this.$store.commit('users/storeData', (await this.$axios.get(`${process.env.SERVER_API}/users/`)).data)
    },
    methods: {
      editItem(user){
        this.$store.commit("user/storeId", user.id);
        this.$store.commit("user/storeEmail", user.email);
        this.$store.commit("user/storePassword", user.password);
      },
      async deleteItem(id){
        await this.$axios.delete(`${process.env.SERVER_API}/users/` + id);
        this.$store.commit(
          "users/storeData",
          (await this.$axios.get(`${process.env.SERVER_API}/users/`)).data
        );
      },

    },
  }
</script>

<style>

</style>
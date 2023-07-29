from channels.consumer import SyncConsumer, AsyncConsumer
from channels.exceptions import StopConsumer
from time import sleep
import asyncio
import json
from asgiref.sync import async_to_sync ## এর মাধ্যমে async এর সকল Proparty কে sync এ ব্যবহার করার যায়

from channels.db import database_sync_to_async ## মুলত Channel Layout Django ORM support করে না, তাই এর সাহায্যে তা support করানো হয়েছে।
from app.models import Group, Chat

## NOTE Channel Layer -> দুটি বা multiple Instance নিজেদের মধ্যে জাতে Communicate করতে পারে তার জন্যে Channel Layer ব্যবহার করা হয়।

class MySyncConsumer(SyncConsumer):

    def websocket_connect(self, event):
        print("Connect...........")

        print("Channel Layer = ", self.channel_layer)  
        print("Channel Name = ", self.channel_name)
        print("Consumer Group Name = ", self.scope['url_route']['kwargs']['group_name'])  


        self.groupName = self.scope['url_route']['kwargs']['group_name']  # Consumers এ self.request এর পরিবর্তে self.scope


        ## NOTE Add a channel to a new or existing group
        async_to_sync(self.channel_layer.group_add)(
            # 'Bangladesh',   # Group Name
            self.groupName,   # Group Name
            self.channel_name
        )

        self.send({
            "type": "websocket.accept",
        })




    def websocket_receive(self, event):
        print("Receive...........")
        
        # NOTE Data base এ Message Save করা ইয়েছে,--------------------------
        python_dic = json.loads(event['text'])

        print("------------------------------------")
        print("Message is: ", event['text'])
        print(f"Data Type = {type(python_dic)} and Python Data = {python_dic}")
        print("Massage = ", python_dic['msg'])
        print("Login User = ", self.scope['user'])
        print("------------------------------------")
        
        ## Find Group Object
        ## এখানে Group obj find করা হয়েছে জাগে আমরা সেই Group এর Chat Table এ ঐ massage গুলো save করাতে পারি।
        # if Group.objects.filter(name = self.groupName).exists():
        group = Group.objects.get(name = self.groupName)


        if self.scope['user'].is_authenticated:
            ## Create a new chat object
            chat = Chat(
                group = group,
                user = self.scope['user'],
                content = python_dic['msg'],
            ).save()
            ##__________________________________________________________________

            ## username msg এর সাথে fontend এ show করানোর জন্যে একটি variable এ store করা হয়েছে
            python_dic['user'] = self.scope['user'].username   

            ## Display the massage in user chat page
            async_to_sync(self.channel_layer.group_send)(
                self.groupName,{
                    'type': 'chat.message',   # Chat Message Hendler টি নিচে Creat করা হয়েছে
                    # 'message': event['text'],
                    'message': json.dumps(python_dic),
                }
            )
        else:
            self.send({
                "type": "websocket.send",
                "text": json.dumps({"msg": "Login Required", "user": "unknown"})
            })

    ## Chat Message Event Hendler টি Create করার জন্যে . এর যায় গায় শুধু _ দিতে হবে chat.message কে chat_message লিখতে হবে।
    def chat_message(self, event):
        print("------------------------------------")    
        print('Event....', event)
        print('Data', event['message']) # Data type is string 

        # এখন আমাদের এই data টি কে Text area তে দেখাতে চাইলে তা Send করতে হবে
        self.send({
            "type": "websocket.send",
            'text': event['message'],
        })
        print("------------------------------------")





    def websocket_disconnect(self, event):
        print("Disconnect...........")

        print("Channel Layer = ", self.channel_layer)  
        print("Channel Name = ", self.channel_name)

        ## NOTE Add a channel to a new or existing group
        async_to_sync(self.channel_layer.group_discard)(
            self.groupName,   # Group Name
            self.channel_name
        )
        raise StopConsumer()













class MyAsyncConsumer(AsyncConsumer):

    async def websocket_connect(self, event):
        print("Connect...........")
        print("Channel Layer = ", self.channel_layer)  
        print("Channel Name = ", self.channel_name)
        print("Consumer Group Name = ", self.scope['url_route']['kwargs']['group_name'])  


        self.groupName = self.scope['url_route']['kwargs']['group_name']  # Consumers এ self.request এর পরিবর্তে self.scope


        ## NOTE Add a channel to a new or existing group
        await self.channel_layer.group_add(
            # 'Bangladesh',   # Group Name
            self.groupName,   # Group Name
            self.channel_name
        )

        await self.send({
            "type": "websocket.accept",
        })



    async def websocket_receive(self, event):
        print("Receive...........")

        # NOTE Data base এ Message Save করা ইয়েছে,--------------------------
        python_dic = json.loads(event['text'])

        print("------------------------------------")
        print("Message is: ", event['text'])
        print(f"Data Type = {type(python_dic)} and Python Data = {python_dic}")
        print("Massage = ", python_dic['msg'])
        print("Login User = ", self.scope['user'])
        print("------------------------------------")
        
        ## এখানে Group obj find করা হয়েছে জাগে আমরা সেই Group এর Chat Table এ ঐ massage গুলো save করাতে পারি।
        # if Group.objects.filter(name = self.groupName).exists():
        group = await database_sync_to_async(Group.objects.get)(name = self.groupName)

        if self.scope['user'].is_authenticated:
            chat = Chat(
                group = group,
                user = self.scope['user'],
                content = python_dic['msg'],
            )
            await database_sync_to_async(chat.save)()
            ##__________________________________________________________________

            ## username msg এর সাথে fontend এ show করানোর জন্যে একটি variable এ store করা হয়েছে
            python_dic['user'] = self.scope['user'].username 

            await self.channel_layer.group_send(
                self.groupName,{
                    'type': 'chat.message',   # Chat Message Hendler টি নিচে Creat করা হয়েছে
                    # 'message': event['text'],
                    'message': json.dumps(python_dic),
                }
            )
        else:
            await self.send({
                "type": "websocket.send",
                "text": json.dumps({"msg": "Login Required", "user": "unknown"})
            })

    ## Chat Message Event Hendler টি Create করার জন্যে . এর যায় গায় শুধু _ দিতে হবে chat.message কে chat_message লিখতে হবে।
    async def chat_message(self, event):
        print("------------------------------------")    
        print('Event....', event)
        print('Data', event['message']) # Data type is string 

        # এখন আমাদের এই data টি কে Text area তে দেখাতে চাইলে তা Send করতে হবে
        await self.send({
            "type": "websocket.send",
            'text': event['message'],
        })
        print("------------------------------------")





    async def websocket_disconnect(self, event):
        print("Disconnect...........")
        print("Channel Layer = ", self.channel_layer)  
        print("Channel Name = ", self.channel_name)

        ## NOTE Add a channel to a new or existing group
        await self.channel_layer.group_discard(
            self.groupName,   # Group Name
            self.channel_name
        )
        raise StopConsumer()
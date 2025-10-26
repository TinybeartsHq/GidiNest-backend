import threading

from django.template.loader import render_to_string

from providers.email import EmailBackEnd



data = EmailBackEnd()



class Email:
 
    @staticmethod
    def send_code(email, code):
        """Sending Verification Email"""
        
        """Call the Email Backend"""
 
        html_content = render_to_string("email/code.html", {
            "code": code})
        # data.send_grid(
        #         template=html_content, email=email, subject="Verification Code"
        #     )
        t1 = threading.Thread(
            args=data.send_grid(
                template=html_content, email=email, subject="Verification Code"
            )
        )
        t1.start()
        pass

     
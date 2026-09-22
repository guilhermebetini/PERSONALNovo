from django.shortcuts import render


def pagina(nome):
    def view(request):
        return render(request, nome)

    return view

class HomeController < ApplicationController
  def show
    render html: <<~HTML.html_safe
      <main>
        <h1>#{Current.brand || "INK Receipts"}</h1>
        <p>Shared commercial platform for INK, BLKBXS, MAND8, and DUE.</p>
      </main>
    HTML
  end
end
